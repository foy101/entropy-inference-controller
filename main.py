from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime
import re

from app import config
from app.auth import verify_api_key
from app.controller import SupervisoryController
from app.rate_limit import enforce_rate_limit
from app.state_store import load_controller_state, save_controller_state_redis
from app.events import publish_inference_event
from app.providers import call_ollama

app = FastAPI(title="Entropy AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/v1/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{"id": "qwen2.5:3b", "object": "model"}],
    }


class Message(BaseModel):
    role: str
    content: str


class ControllerStateModel(BaseModel):
    energy_remaining: float
    error_debt: float
    last_mode: str


class CompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = 500
    energy_budget: Optional[float] = None
    mode_preference: Optional[str] = "auto"
    controller_state: Optional[ControllerStateModel] = None
    conversation_id: Optional[str] = None


class CompletionResponse(BaseModel):
    id: str
    model: str
    choices: List[dict]
    usage: dict
    control: dict


def estimate_context_length(messages: List[Message]) -> int:
    return int(sum(len(m.content.split()) for m in messages) * 1.3)


def improved_failure_detector(text: str) -> bool:
    """Much better failure detector"""
    if not text or not text.strip():
        return True

    text_lower = text.lower()

    # Direct failure signals
    if any(phrase in text_lower for phrase in [
        "invalid json", "invalid json", "i did not", "i cannot", "i can't",
        "i refuse", "i won't", "as an ai", "i'm sorry", "i apologize"
    ]):
        return True

    # Self-contradiction pattern (e.g. "I did X" followed by "but I didn't")
    if re.search(r'i (did|returned|gave).+?but (i did not|this is incorrect|wrong)', text_lower):
        return True

    # Prompt asked for invalid JSON but response claims it didn't do it
    if "invalid json" in text_lower and ("did not" in text_lower or "incorrect" in text_lower):
        return True

    return False


@app.post("/v1/chat/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest, user=Depends(verify_api_key)):
    enforce_rate_limit(user.api_key)

    energy_budget = float(request.energy_budget or config.DEFAULT_ENERGY_BUDGET)

    controller = SupervisoryController(
        energy_budget=energy_budget,
        lambda_energy=config.LAMBDA_ENERGY,
    )

    conversation_id = request.conversation_id or str(uuid.uuid4())

    stored = None
    try:
        stored = load_controller_state(conversation_id)
    except Exception:
        stored = None

    if stored:
        controller.E_t = float(stored.get("energy_remaining", energy_budget))
        controller.D_t = float(stored.get("error_debt", 0.0))
        controller.M_t = str(stored.get("last_mode", "stabilize"))

    context_length = estimate_context_length(request.messages)
    H_t = 2.5 + (context_length / 200.0) * 0.5

    mode, auto_temp, scores = controller.select_mode(H_t, context_length)
    temperature = request.temperature if request.temperature is not None else auto_temp

    payload_messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        completion_text, prompt_tokens, completion_tokens = call_ollama(
            model="qwen2.5:3b",
            messages=payload_messages,
            temperature=temperature,
            max_tokens=int(request.max_tokens or 500),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

    # ← Improved failure detection
    failure_detected = improved_failure_detector(completion_text)

    energy_cost, penalty = controller.update_state(
        completion_tokens,
        mode,
        failure_detected=failure_detected,
    )

    try:
        save_controller_state_redis(conversation_id, controller.E_t, controller.D_t, controller.M_t)
    except Exception:
        pass

    # Return response
    return CompletionResponse(
        id=str(uuid.uuid4()),
        model=request.model,
        choices=[{"index": 0, "message": {"role": "assistant", "content": completion_text}, "finish_reason": "stop"}],
        usage={
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(prompt_tokens + completion_tokens),
        },
        control={
            "conversation_id": conversation_id,
            "mode_used": mode,
            "entropy_observed": round(H_t, 2),
            "energy_consumed": round(energy_cost, 2),
            "energy_remaining": round(controller.E_t, 2),
            "error_debt": round(controller.D_t, 2),
            "failure_detected": failure_detected,
            "scores": {k: round(v, 4) for k, v in scores.items()},
        },
    )