# File: cortexfeed/config/settings.py

import os
from dotenv import load_dotenv

from cortexfeed.config.paths import SESSIONS_DIR

load_dotenv()

# Ollama

OLLAMA_HOST = os.getenv("OLLAMA_URL", "http://localhost:11434")

OLLAMA_GENERATE = f"{OLLAMA_HOST}/api/generate"
OLLAMA_CHAT = f"{OLLAMA_HOST}/api/chat"
OLLAMA_TAGS = f"{OLLAMA_HOST}/api/tags"

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "mistral")

SYSTEM_PROMPT = (
    "You are a senior software engineer. "
    "Analyze code, logs, terminal output, and project context. "
    "Give concrete debugging guidance."
)

# File handling

MAX_FILE_KB = int(os.getenv("MAX_FILE_KB", 256))

# Watcher

WATCH_INTERVAL = int(os.getenv("WATCH_INTERVAL", 2))

# Investigation

INVESTIGATION_SESSIONS_ROOT = SESSIONS_DIR