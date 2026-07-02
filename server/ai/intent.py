from cortexfeed.core import ai
from cortexfeed.config import DEFAULT_MODEL

INTENT_SYSTEM = """
You are a coding assistant analyzer. Given a conversation between a developer and an AI, extract:
1. What the AI last suggested or asked the developer to do
2. What the most logical next step is
3. Which files are likely relevant

Respond ONLY in this exact JSON format, no other text:
{
  "last_ai_action": "brief description of what AI last said",
  "next_step": "the single most logical next action",
  "suggested_intent": "ready-to-use description the developer can send as next prompt",
  "likely_files": ["file1.dart", "file2.py"]
}
"""


def analyze_conversation(conversation: str, project_path: str = "", model: str = DEFAULT_MODEL) -> dict:
    """
    Analyze a conversation and extract intent + suggested next step.
    Returns a dict with next_step, suggested_intent, likely_files.
    """
    if not conversation or len(conversation.strip()) < 10:
        return {
            "last_ai_action": "No conversation provided",
            "next_step": "Start a new conversation",
            "suggested_intent": "",
            "likely_files": []
        }

    prompt = (
        f"Here is the conversation to analyze:\n\n"
        f"{conversation[-4000:]}\n\n"  # last 4000 chars to stay within context
        f"Project path: {project_path if project_path else 'unknown'}\n\n"
        f"Extract the intent and next step."
    )

    import json
    response = ai.ask(prompt, model=model, system=INTENT_SYSTEM)

    try:
        # strip any markdown fences if model adds them
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        result = json.loads(clean.strip())
        return result
    except Exception:
        # fallback if model doesn't return valid JSON
        return {
            "last_ai_action": "Could not parse",
            "next_step": "Review conversation manually",
            "suggested_intent": response[:500],
            "likely_files": []
        }