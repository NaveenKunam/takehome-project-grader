import os
from typing import Any, Dict, List, Optional

import httpx


GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")


def _groq_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def groq_chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "llama-3.1-70b-versatile",
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> str:
    api_key = _groq_key()
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY")

    url = f"{GROQ_BASE_URL.rstrip('/')}/chat/completions"
    payload: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=payload)

    if resp.status_code >= 400:
        raise RuntimeError(f"{resp.status_code} {resp.text}")

    data = resp.json()
    choices: List[Dict[str, Any]] = data.get("choices", []) or []
    if not choices:
        raise RuntimeError(f"No choices in response: {data}")

    message: Optional[Dict[str, Any]] = choices[0].get("message")
    content = (message or {}).get("content") if isinstance(message, dict) else None
    content = (content or "").strip()
    if not content:
        raise RuntimeError(f"Empty content response: {data}")
    return content

