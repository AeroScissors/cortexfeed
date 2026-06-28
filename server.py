"""
server.py — cortexfeed local HTTP server
Chrome extension talks to this on localhost:5050
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from cortexfeed.core.context import resolve_paths, format_for_prompt
from cortexfeed.core import ollama
from cortexfeed.config import DEFAULT_MODEL
from cortexfeed.api.investigate_api import investigate_bp
from cortexfeed.api.session_api import session_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(investigate_bp)
app.register_blueprint(session_bp)

model = DEFAULT_MODEL


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'model': model})


# ── Smart prompt templates ────────────────────────────────
PROMPT_INTROS = {
    'debug':    'I have a bug I need help debugging.',
    'code':     'I need help writing or implementing code.',
    'explain':  'I need something explained clearly.',
    'research': 'I need accurate, up-to-date information on this topic.',
    'design':   'I need help with system design or architecture.',
    'general':  'I need help with the following.',
}

PROMPT_OUTROS = {
    'debug':    'Please identify the root cause and provide a specific fix.',
    'code':     'Please write the implementation. Keep it clean and add comments where helpful.',
    'explain':  'Please explain clearly with examples where useful.',
    'research': 'Please provide accurate, current information.',
    'design':   'Please give architectural recommendations with trade-offs.',
    'general':  'Please help me with this.',
}


@app.route('/build-prompt', methods=['POST'])
def build_prompt():
    import os
    data = request.json
    conversation        = data.get('conversation', '')
    intent              = data.get('intent', '')
    expected            = data.get('expected', '')
    actual              = data.get('actual', '')
    files               = data.get('files', [])
    target              = data.get('target', 'any AI assistant')
    project_path        = data.get('project_path', '')
    conversation_summary = data.get('conversation_summary', '')
    task_type           = data.get('task_type', 'general')
    github_context      = data.get('github_context')   # dict or None
    extra_context       = data.get('extra_context', '') # selected text from right-click

    print(f"[PROMPT] task_type={task_type} summary_len={len(conversation_summary)}")

    # Resolve file contents
    file_context = ""
    if files:
        all_files = []
        for pat in files:
            full = os.path.join(project_path, pat) if project_path else pat
            all_files.extend(resolve_paths(full))
        if all_files:
            file_context = format_for_prompt(all_files)

    # Build prompt using task-specific template
    intro = PROMPT_INTROS.get(task_type, PROMPT_INTROS['general'])
    outro = PROMPT_OUTROS.get(task_type, PROMPT_OUTROS['general'])

    sections = [intro]

    # Conversation context
    if conversation_summary:
        sections.append(f"Context from our previous conversation:\n{conversation_summary}")
    elif conversation:
        sections.append(f"Here is the conversation so far:\n\n{conversation[:4000]}")

    # GitHub repo context (Feature 3)
    if github_context:
        gh_text = f"GitHub Repository: {github_context.get('owner','')}/{github_context.get('repo','')}\n"
        if github_context.get('readme'):
            gh_text += f"\nREADME:\n{github_context['readme'][:1500]}"
        if github_context.get('fileTree'):
            gh_text += f"\nFile structure:\n{github_context['fileTree']}"
        sections.append(gh_text)

    # Intent / problem description
    if intent:
        label = 'Bug description' if task_type == 'debug' else 'What I need'
        sections.append(f"{label}:\n{intent}")

    # Selected text from right-click (Feature 5)
    if extra_context:
        sections.append(f"Additional context:\n{extra_context}")

    # File contents
    if file_context:
        sections.append(f"Relevant files:\n\n{file_context}")

    # Expected / actual (always shown for debug, optional otherwise)
    if expected:
        sections.append(f"Expected behavior:\n{expected}")
    if actual:
        sections.append(f"Current behavior / what is going wrong:\n{actual}")

    sections.append(f"{outro}\n\nI am sending this to {target}.")

    built_prompt = "\n\n---\n\n".join(sections)
    return jsonify({'status': 'ok', 'prompt': built_prompt})


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    response = ollama.ask(question, model=model)
    return jsonify({'response': response})


@app.route('/set-model', methods=['POST'])
def set_model():
    global model
    data = request.json
    new_model = data.get('model', '')
    if new_model:
        model = new_model
        return jsonify({'status': 'ok', 'model': model})
    return jsonify({'error': 'No model provided'}), 400


@app.route('/repo-intel', methods=['POST'])
def repo_intel():
    data = request.json
    question = data.get('question', '').strip()
    project_path = data.get('project_path', '').strip()

    if not question:
        return jsonify({'error': 'No question provided'}), 400
    if not project_path:
        return jsonify({'error': 'No project_path provided'}), 400

    try:
        from pathlib import Path
        from cortexfeed.intelligence.bootstrap import build_repository_intelligence

        facade = build_repository_intelligence(Path(project_path))
        result = facade.ask(question)

        return jsonify({
            'status': 'ok',
            'capability': result.capability,
            'answer': result.answer,
            'confidence': result.confidence,
            'evidence': result.evidence,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_model():
    return model


from server.routes import analyze, files, classify
analyze.register(app, get_model)
files.register(app, get_model)
classify.register(app, get_model)


if __name__ == '__main__':
    print("cortexfeed server starting on http://localhost:5050")
    print("Chrome extension can now connect.")
    print("Investigation API available at:")
    print("  POST /investigate")
    print("  POST /investigate/prompt")
    print("  GET  /sessions")
    print("  GET  /sessions/<project_name>")
    print("  DELETE /sessions/<project_name>")
    print("  POST /repo-intel")
    print("  POST /classify")
    app.run(host='localhost', port=5050, debug=False)