import json
import time
import redis
from app import config
from app.models import SessionLocal, ControllerState

_redis = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)

STATE_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

def _redis_key(conversation_id: str) -> str:
    return f"cs:{conversation_id}"

def load_controller_state(conversation_id: str):
    raw = _redis.get(_redis_key(conversation_id))
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass

    db = SessionLocal()
    try:
        state = db.query(ControllerState).filter(ControllerState.id == conversation_id).first()
        if not state:
            return None
        payload = {
            "energy_remaining": float(state.energy_remaining),
            "error_debt": float(state.error_debt),
            "last_mode": str(state.last_mode),
            "updated_at": time.time(),
        }
        _redis.setex(_redis_key(conversation_id), STATE_TTL_SECONDS, json.dumps(payload))
        return payload
    finally:
        db.close()

def save_controller_state_redis(conversation_id: str, energy_remaining: float, error_debt: float, last_mode: str):
    payload = {
        "energy_remaining": float(energy_remaining),
        "error_debt": float(error_debt),
        "last_mode": str(last_mode),
        "updated_at": time.time(),
    }
    _redis.setex(_redis_key(conversation_id), STATE_TTL_SECONDS, json.dumps(payload))
    return payload
