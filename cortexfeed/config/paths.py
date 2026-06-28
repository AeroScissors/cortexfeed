# File: cortexfeed/config/paths.py

from pathlib import Path

# Root of the cortexfeed data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Investigation sessions
SESSIONS_DIR = DATA_DIR / "sessions"

# Embeddings and indexes
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
INDEXES_DIR = DATA_DIR / "indexes"
CACHE_DIR = DATA_DIR / "cache"


def ensure_data_dirs() -> None:
    """Create all required data directories if they don't exist."""
    for directory in (
        SESSIONS_DIR,
        EMBEDDINGS_DIR,
        INDEXES_DIR,
        CACHE_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)