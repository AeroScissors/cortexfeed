# File: cortexfeed/config/__init__.py

from cortexfeed.config.settings import (
    OLLAMA_HOST,
    OLLAMA_GENERATE,
    OLLAMA_CHAT,
    OLLAMA_TAGS,
    DEFAULT_MODEL,
    SYSTEM_PROMPT,
    MAX_FILE_KB,
    WATCH_INTERVAL,
    INVESTIGATION_SESSIONS_ROOT,
)

__all__ = [
    "OLLAMA_HOST",
    "OLLAMA_GENERATE",
    "OLLAMA_CHAT",
    "OLLAMA_TAGS",
    "DEFAULT_MODEL",
    "SYSTEM_PROMPT",
    "MAX_FILE_KB",
    "WATCH_INTERVAL",
    "INVESTIGATION_SESSIONS_ROOT",
]