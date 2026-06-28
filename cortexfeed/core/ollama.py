import json
import requests
from cortexfeed.config import OLLAMA_GENERATE, OLLAMA_CHAT, OLLAMA_TAGS, DEFAULT_MODEL, SYSTEM_PROMPT


def check_ollama() -> list | None:
    """Check if Ollama is running, return list of available models."""
    try:
        r = requests.get(OLLAMA_TAGS, timeout=3)
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return None


def ask(prompt: str, model: str = DEFAULT_MODEL, system: str = SYSTEM_PROMPT) -> str:
    """Single prompt, return full response string."""
    payload = {"model": model, "prompt": prompt, "system": system, "stream": False}
    try:
        r = requests.post(OLLAMA_GENERATE, json=payload, timeout=120)
        return r.json().get("response", "").strip()
    except Exception as e:
        return f"[Ollama error: {e}]"


def stream(prompt: str, model: str = DEFAULT_MODEL, system: str = SYSTEM_PROMPT):
    """Stream response token by token to terminal."""
    payload = {"model": model, "prompt": prompt, "system": system, "stream": True}
    try:
        with requests.post(OLLAMA_GENERATE, json=payload, stream=True, timeout=120) as r:
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    print(chunk.get("response", ""), end="", flush=True)
                    if chunk.get("done"):
                        break
        print()
    except Exception as e:
        print(f"[Ollama error: {e}]")


def chat(messages: list, model: str = DEFAULT_MODEL) -> str:
    """Multi-turn chat, pass full message history."""
    payload = {"model": model, "messages": messages, "stream": False}
    try:
        r = requests.post(OLLAMA_CHAT, json=payload, timeout=120)
        return r.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[Ollama error: {e}]"