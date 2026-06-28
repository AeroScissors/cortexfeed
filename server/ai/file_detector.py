import os
import re


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


def scan_project(project_path: str) -> list:
    """Scan project folder and return list of all code files."""
    files = []
    if not project_path or not os.path.exists(project_path):
        return files

    for root, dirs, filenames in os.walk(project_path):
        # skip unwanted dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in CODE_EXTENSIONS:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, project_path)
                files.append(rel_path.replace("\\", "/"))

    return files


def extract_keywords(text: str) -> list:
    """Extract likely file/class/function names from conversation text."""
    keywords = []

    # filenames with extensions
    file_pattern = re.findall(r'\b[\w/]+\.\w{2,6}\b', text)
    keywords.extend(file_pattern)

    # dart/python class names (CamelCase)
    class_pattern = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
    keywords.extend([k.lower() for k in class_pattern])

    # snake_case identifiers
    snake_pattern = re.findall(r'\b[a-z]+(?:_[a-z]+){1,}\b', text)
    keywords.extend(snake_pattern)

    return list(set(keywords))


def score_file(filepath: str, keywords: list) -> int:
    """Score a file path based on how many keywords it matches."""
    score = 0
    filepath_lower = filepath.lower()
    for kw in keywords:
        if kw.lower() in filepath_lower:
            score += 1
    return score


def detect_relevant_files(
    conversation: str,
    project_path: str,
    likely_files: list = None,
    max_results: int = 6
) -> list:
    """
    Given a conversation and project path, return the most relevant files.
    Combines AI suggestions with keyword matching.
    """
    all_files = scan_project(project_path)
    if not all_files:
        return likely_files or []

    keywords = extract_keywords(conversation)

    # score every file
    scored = []
    for f in all_files:
        score = score_file(f, keywords)

        # boost files explicitly mentioned by AI
        if likely_files:
            for suggested in likely_files:
                if suggested.lower() in f.lower() or f.lower() in suggested.lower():
                    score += 5

        if score > 0:
            scored.append((f, score))

    # sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    return [f for f, _ in scored[:max_results]]