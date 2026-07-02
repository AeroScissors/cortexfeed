"""
cortexfeed/core/ai.py — unified AI backend

Set AI_BACKEND in .env to switch between providers:
  AI_BACKEND=ollama      (default, free, local — requires Ollama)
  AI_BACKEND=openai      (requires OPENAI_API_KEY)
  AI_BACKEND=anthropic   (requires ANTHROPIC_API_KEY)
"""

import requests
from cortexfeed.config import (
    AI_BACKEND, SYSTEM_PROMPT, DEFAULT_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
)


def ask(prompt: str, model: str = None, system: str = SYSTEM_PROMPT) -> str:
    """Send a prompt and return the response string. Backend chosen by AI_BACKEND env var."""
    backend = AI_BACKEND.lower().strip()

    if backend == "openai":
        return _ask_openai(prompt, model or OPENAI_MODEL, system)
    elif backend == "anthropic":
        return _ask_anthropic(prompt, model or ANTHROPIC_MODEL, system)
    else:
        # Default: Ollama
        from cortexfeed.core import ollama
        return ollama.ask(prompt, model or DEFAULT_MODEL, system)


def backend_label() -> str:
    """Return a human-readable label for the current backend + model."""
    b = AI_BACKEND.lower().strip()
    if b == "openai":
        return f"openai/{OPENAI_MODEL}"
    elif b == "anthropic":
        return f"anthropic/{ANTHROPIC_MODEL}"
    else:
        return f"ollama/{DEFAULT_MODEL}"


def is_available() -> bool:
    """Quick check — can we reach the configured backend?"""
    b = AI_BACKEND.lower().strip()
    try:
        if b == "openai":
            if not OPENAI_API_KEY:
                return False
            r = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                timeout=5,
            )
            return r.status_code == 200

        elif b == "anthropic":
            if not ANTHROPIC_API_KEY:
                return False
            # Anthropic doesn't have a lightweight ping — just check key is set
            return bool(ANTHROPIC_API_KEY)

        else:
            # Ollama
            from cortexfeed.core import ollama
            return ollama.check_ollama() is not None

    except Exception:
        return False


# ── OpenAI ────────────────────────────────────────────────

def _ask_openai(prompt: str, model: str, system: str) -> str:
    if not OPENAI_API_KEY:
        return "[OpenAI error: OPENAI_API_KEY not set in .env]"
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                "max_tokens": 2048,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[OpenAI error: {e}]"


# ── Anthropic ─────────────────────────────────────────────

def _ask_anthropic(prompt: str, model: str, system: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "[Anthropic error: ANTHROPIC_API_KEY not set in .env]"
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
            json={
                "model":      model,
                "max_tokens": 2048,
                "system":     system,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        return f"[Anthropic error: {e}]"
