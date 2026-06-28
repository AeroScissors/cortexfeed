import os
import glob
import hashlib
import subprocess
from cortexfeed.config import MAX_FILE_KB


def read_file(path: str) -> str:
    """Read a file safely, truncate if too large."""
    try:
        size = os.path.getsize(path)
        limit = MAX_FILE_KB * 1024
        if size > limit:
            content = open(path, errors="replace").read(limit)
            return f"[Truncated — showing first {MAX_FILE_KB}KB of {size//1024}KB]\n{content}"
        return open(path, errors="replace").read()
    except Exception as e:
        return f"[Could not read {path}: {e}]"


def file_hash(path: str) -> str:
    """MD5 hash of a file for change detection."""
    try:
        return hashlib.md5(open(path, "rb").read()).hexdigest()
    except Exception:
        return ""


def resolve_paths(pattern: str) -> list:
    """Expand globs and directories into a flat file list."""
    paths = []
    for p in glob.glob(pattern, recursive=True):
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    paths.append(os.path.join(root, f))
        else:
            paths.append(p)
    return paths


def format_for_prompt(paths: list) -> str:
    """Format multiple files into a single prompt-ready string."""
    parts = []
    for p in paths:
        content = read_file(p)
        parts.append(f"=== FILE: {p} ===\n{content}\n")
    return "\n".join(parts)


def run_command(cmd: str) -> tuple:
    """Run a shell command, return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out after 60s", 1
    except Exception as e:
        return "", str(e), 1