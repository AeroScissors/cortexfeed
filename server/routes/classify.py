"""
classify.py — task classifier and AI router
POST /classify  → { task_type, recommended_ai, ai_display, reason }
"""

import re
from flask import request, jsonify


# ── Classification patterns ───────────────────────────────

TASK_PATTERNS = {
    "debug": [
        r'\b(error|bug|crash|exception|traceback|stack.?trace|not working|broken|fails?|failing|fix|404|500|undefined|nan|null pointer|wrong output|unexpected)\b',
        r'\b(why (is|does|isn\'t|doesn\'t)|what went wrong|can\'t figure|investigate|diagnose)\b',
    ],
    "research": [
        r'\b(latest|current|today|2025|2026|news|recent|new version|release)\b',
        r'\b(best (library|tool|framework|approach)|compare|vs\.?|versus|which (is|should)|what.s (the )?best)\b',
        r'\b(search|look up|find information|what.s new|up.?to.?date)\b',
    ],
    "code": [
        r'\b(implement|write|create|build|generate|scaffold|refactor|add (a |the )?(function|method|class|component|endpoint|route))\b',
        r'\b(how to (write|implement|create|build)|make (a|an|the)|code for)\b',
    ],
    "explain": [
        r'\b(explain|what (is|are|does)|how (does|do|would|should)|understand|meaning|definition|walk me through)\b',
    ],
    "design": [
        r'\b(architecture|design|schema|structure|plan|diagram|flow|organize|how (should|would) (i|we) (structure|organize|design|approach))\b',
        r'\b(best practice|pattern|convention|clean|scalable)\b',
    ],
}

# Which AI handles each task type best, and why
AI_ROUTING = {
    "debug":    ("claude",   "Claude handles long-context debugging and tracing best"),
    "code":     ("claude",   "Claude is strongest at code generation and review"),
    "explain":  ("claude",   "Claude gives thorough, structured explanations"),
    "research": ("gemini",   "Gemini has live web access for current information"),
    "design":   ("claude",   "Claude excels at architecture and system design"),
    "general":  ("claude",   "Claude handles complex open-ended tasks best"),
}

AI_DISPLAY = {
    "claude":  "Claude",
    "chatgpt": "ChatGPT",
    "gemini":  "Gemini",
}


def classify_task(text: str) -> tuple:
    """
    Rule-based task classifier — fast, no Ollama required.
    Returns (task_type, recommended_ai, reason).
    """
    text_lower = text.lower()
    scores = {task: 0 for task in TASK_PATTERNS}

    for task, patterns in TASK_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            scores[task] += len(matches)

    best_task = max(scores, key=scores.get)
    if scores[best_task] == 0:
        best_task = "general"

    ai, reason = AI_ROUTING.get(best_task, AI_ROUTING["general"])
    return best_task, ai, reason


def register(app, get_model):

    @app.route('/classify', methods=['POST'])
    def classify():
        """
        Classify a task and recommend the best AI for it.

        Body: { "intent": "...", "conversation": "..." }

        Returns:
        {
          "status":         "ok",
          "task_type":      "debug",
          "recommended_ai": "claude",
          "ai_display":     "Claude",
          "reason":         "Claude handles long-context debugging best"
        }
        """
        data = request.json or {}
        text = (data.get('intent') or '') + ' ' + (data.get('conversation') or '')[:2000]

        if not text.strip():
            return jsonify({'error': 'No text provided'}), 400

        task_type, recommended_ai, reason = classify_task(text)

        return jsonify({
            'status':         'ok',
            'task_type':      task_type,
            'recommended_ai': recommended_ai,
            'ai_display':     AI_DISPLAY.get(recommended_ai, recommended_ai),
            'reason':         reason,
        })
