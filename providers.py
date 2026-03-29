import ollama

def call_ollama(model: str, messages: list[dict], temperature: float, max_tokens: int):
    """Free local inference via Ollama"""
    response = ollama.chat(
        model=model,
        messages=messages,
        options={
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    )
    text = response['message']['content']
    # Rough token estimates (Ollama doesn't give exact counts)
    prompt_tokens = len(str(messages))
    completion_tokens = len(text.split())
    return text, prompt_tokens, completion_tokens