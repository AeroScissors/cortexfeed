import re
from flask import request, jsonify
from server.ai.intent import analyze_conversation
from server.ai.file_detector import detect_relevant_files
from cortexfeed.core import ai


def _rule_based_summary(conversation: str) -> str:
    """
    Fallback summarizer when Ollama is offline.
    Extracts the last AI message block and key findings
    from the conversation text.
    """
    lines = conversation.strip().splitlines()

    # grab last 30 non-empty lines as the tail
    tail = [l.strip() for l in lines if l.strip()][-30:]

    # pull out any HTTP method mentions (GET /promise etc)
    routes = re.findall(r'\b(GET|POST|PATCH|PUT|DELETE)\s+(/[\w/.<>?=&_-]+)', conversation)
    route_mentions = [f"{m} {p}" for m, p in routes[-3:]]

    # pull out file mentions
    files = re.findall(r'[\w/]+\.\w{2,5}', conversation)
    seen = []
    for f in files:
        if f not in seen and not f.startswith('http'):
            seen.append(f)
    file_mentions = seen[:5]

    parts = []

    if route_mentions:
        parts.append(f"Routes discussed: {', '.join(route_mentions)}.")

    if file_mentions:
        parts.append(f"Files involved: {', '.join(file_mentions)}.")

    # include the last meaningful tail as context
    tail_text = ' '.join(tail[-10:])
    if tail_text:
        parts.append(f"Last context: {tail_text[:400]}")

    return ' '.join(parts) if parts else conversation[:600]


def _rule_based_intent(conversation: str) -> dict:
    """
    Fallback intent extractor when Ollama is offline.
    Scans for 404s, missing routes, file requests, and next steps.
    """
    text = conversation.lower()

    # detect likely next step from common patterns
    next_step = "Review conversation and continue debugging"
    suggested_intent = ""
    last_ai_action = ""

    if "paste these files" in text or "paste the files" in text:
        last_ai_action = "AI requested specific files to be pasted"
        next_step = "Paste the requested files into the conversation"
        # extract what files were asked for
        file_matches = re.findall(r'`([^`]+\.\w{2,5})`', conversation)
        if file_matches:
            files_list = ', '.join(file_matches[-4:])
            suggested_intent = f"Here are the requested files: {files_list}"

    elif "what i need next" in text or "next step" in text:
        last_ai_action = "AI outlined next steps"
        next_step = "Follow the AI's outlined next steps"

    elif "404" in text and ("missing" in text or "not found" in text):
        last_ai_action = "Identified missing route causing 404"
        routes = re.findall(r'\b(GET|POST|PATCH|PUT|DELETE)\s+(/[\w/.<>?=&_-]+)', conversation)
        if routes:
            method, path = routes[-1]
            next_step = f"Implement missing {method} {path} endpoint"
            suggested_intent = f"Implement {method} {path} endpoint as discussed"

    elif "serialization" in text or "contract" in text or "tojson" in text or "fromjson" in text:
        last_ai_action = "Investigating JSON serialization contract mismatch"
        next_step = "Compare toJson/fromJson between server and client models"
        suggested_intent = "Verify JSON contract between server and Flutter models"

    # extract likely files from backtick mentions
    likely_files = re.findall(r'`([^`\n]+\.\w{2,5})`', conversation)
    likely_files = list(dict.fromkeys(likely_files))[:6]  # dedupe, keep order

    return {
        "last_ai_action": last_ai_action or "Analyzed conversation",
        "next_step": next_step,
        "suggested_intent": suggested_intent,
        "likely_files": likely_files
    }


def summarize_conversation(conversation: str, model: str) -> str:
    """Summarize a long conversation into 2-3 sentences using Ollama."""
    prompt = (
        f"Summarize this developer debugging conversation in 2-3 sentences. "
        f"Focus on: what problem is being solved, what has been found so far, and what the next step is. "
        f"Be very concise.\n\n{conversation[-4000:]}"
    )
    system = "You are a technical summarizer. Output only the summary, no preamble."
    return ai.ask(prompt, model=model, system=system)


def register(app, get_model):

    @app.route('/analyze', methods=['POST'])
    def analyze():
        data = request.json
        conversation = data.get('conversation', '')
        project_path = data.get('project_path', '')

        if not conversation:
            return jsonify({'error': 'No conversation provided'}), 400

        model = get_model()
        print(f"\n[ANALYZE] model={model} project={project_path}")
        print(f"[ANALYZE] conversation length={len(conversation)}")

        # try Ollama-based intent analysis, fall back to rule-based
        try:
            result = analyze_conversation(conversation, project_path, model)
            print(f"[ANALYZE] result={result}")
        except Exception as e:
            print(f"[ANALYZE] Ollama failed, using rule-based fallback: {e}")
            result = _rule_based_intent(conversation)

        # if Ollama returned empty suggested_intent, try rule-based too
        if not result.get('suggested_intent'):
            fallback = _rule_based_intent(conversation)
            if fallback.get('suggested_intent'):
                result['suggested_intent'] = fallback['suggested_intent']
            if not result.get('next_step') or result.get('next_step') == 'Review conversation manually':
                result['next_step'] = fallback['next_step']
            if not result.get('last_ai_action') or result.get('last_ai_action') == 'Could not parse':
                result['last_ai_action'] = fallback['last_ai_action']
            if not result.get('likely_files'):
                result['likely_files'] = fallback['likely_files']

        try:
            relevant_files = detect_relevant_files(
                conversation=conversation,
                project_path=project_path,
                likely_files=result.get('likely_files', []),
                max_results=6
            )
            print(f"[ANALYZE] detected_files={relevant_files}")
        except Exception as e:
            print(f"[ANALYZE] file detect ERROR: {e}")
            relevant_files = []

        # summarize with Ollama, fall back to rule-based extraction
        summary = ""
        if len(conversation) > 500:
            try:
                summary = summarize_conversation(conversation, model)
                print(f"[ANALYZE] summary={summary}")
            except Exception as e:
                print(f"[ANALYZE] Ollama summary failed, using rule-based: {e}")
                summary = _rule_based_summary(conversation)
        else:
            summary = conversation

        return jsonify({
            'status': 'ok',
            'last_ai_action': result.get('last_ai_action', ''),
            'next_step': result.get('next_step', ''),
            'suggested_intent': result.get('suggested_intent', ''),
            'likely_files': result.get('likely_files', []),
            'detected_files': relevant_files,
            'conversation_summary': summary
        })