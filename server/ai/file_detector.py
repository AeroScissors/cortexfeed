import os
import re
import time


# File extensions to scan
CODE_EXTENSIONS = {
    '.dart', '.py', '.js', '.ts', '.jsx', '.tsx',
    '.json', '.yaml', '.yml', '.env', '.md',
    '.html', '.css', '.sql', '.sh', '.bat'
}

# Folders to always skip
SKIP_DIRS = {
    'node_modules', '.git', 'venv', '.venv', 'build',
    'dist', '__pycache__', '.dart_tool', '.pub-cache',
    'android', 'ios', 'web', 'windows', 'linux', 'macos'
}

# Entry-point files that are almost always relevant
ENTRY_POINTS = {
    'main.py', 'app.py', 'server.py', 'index.py',
    'main.js', 'index.js', 'app.js', 'server.js',
    'main.ts', 'index.ts', 'app.ts',
    'main.dart', 'app.dart',
    'main.go', 'main.rb', 'main.rs',
}

# Max KB to read for content scanning (keep it fast)
CONTENT_SCAN_MAX_KB = 20


def scan_project(project_path: str) -> list[dict]:
    """
    Scan project folder and return list of dicts with path + mtime.
    Returns: [{'path': 'rel/path/file.py', 'mtime': 1234567890.0}]
    """
    files = []
    if not project_path or not os.path.exists(project_path):
        return files

    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in CODE_EXTENSIONS:
                full_path = os.path.join(root, fname)
                try:
                    mtime = os.path.getmtime(full_path)
                except OSError:
                    mtime = 0.0
                rel_path = os.path.relpath(full_path, project_path).replace("\\", "/")
                files.append({'path': rel_path, 'mtime': mtime, 'full': full_path})

    return files


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case so 'UserController' → 'user_controller'."""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def extract_keywords(text: str) -> set[str]:
    """Extract likely file/class/function names from conversation text."""
    keywords = set()

    # Explicit filenames with extensions (keep the stem too)
    for match in re.findall(r'\b([\w/]+)(\.\w{2,6})\b', text):
        full = (match[0] + match[1]).lower()
        stem = match[0].lower()
        keywords.add(full)
        keywords.add(stem)

    # CamelCase identifiers → also add snake_case version
    for name in re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text):
        keywords.add(name.lower())
        keywords.add(camel_to_snake(name))

    # snake_case identifiers
    for name in re.findall(r'\b[a-z]+(?:_[a-z]+){1,}\b', text):
        keywords.add(name)

    # Backtick-quoted identifiers (AI often quotes file names / symbols)
    for name in re.findall(r'`([^`\n]+)`', text):
        keywords.add(name.lower().strip())
        stem = os.path.splitext(name)[0].lower().strip()
        if stem:
            keywords.add(stem)

    # Remove very short noise words
    keywords = {k for k in keywords if len(k) > 2}

    return keywords


def score_file(file_info: dict, keywords: set, now: float) -> float:
    """
    Score a file combining:
    - path keyword matches
    - content keyword matches (small files only)
    - recency boost (modified in last hour / day / week)
    - entry-point boost
    """
    path = file_info['path']
    full = file_info['full']
    mtime = file_info['mtime']
    path_lower = path.lower()
    fname = os.path.basename(path_lower)

    score = 0.0

    # ── 1. Path keyword match ──────────────────────────────
    for kw in keywords:
        if kw in path_lower:
            score += 1.0

    # ── 2. Content scanning ────────────────────────────────
    try:
        size_kb = os.path.getsize(full) / 1024
        if size_kb <= CONTENT_SCAN_MAX_KB:
            with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read().lower()
            for kw in keywords:
                if kw in content:
                    score += 0.5  # content match worth half a path match
    except (OSError, PermissionError):
        pass

    # ── 3. Recency boost ──────────────────────────────────
    age_secs = now - mtime
    if age_secs < 3600:        # modified in last hour
        score += 3.0
    elif age_secs < 86400:     # last day
        score += 2.0
    elif age_secs < 604800:    # last week
        score += 1.0

    # ── 4. Entry-point boost ──────────────────────────────
    if fname in ENTRY_POINTS:
        score += 2.0

    return score


def detect_relevant_files(
    conversation: str,
    project_path: str,
    likely_files: list = None,
    max_results: int = 6
) -> list:
    """
    Return the most relevant files given a conversation and project path.
    Combines AI suggestions, keyword matching, content scanning, and recency.
    """
    all_files = scan_project(project_path)
    if not all_files:
        return likely_files or []

    keywords = extract_keywords(conversation)
    now = time.time()

    scored = []
    for file_info in all_files:
        score = score_file(file_info, keywords, now)

        # Boost files explicitly suggested by the AI intent model
        if likely_files:
            for suggested in likely_files:
                suggested_lower = suggested.lower()
                path_lower = file_info['path'].lower()
                if suggested_lower in path_lower or path_lower in suggested_lower:
                    score += 5.0

        if score > 0:
            # Store full absolute path so callers don't need to re-join
            scored.append((file_info['full'], score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [f for f, _ in scored[:max_results]]
