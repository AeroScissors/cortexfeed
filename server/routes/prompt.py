from flask import request, jsonify
from cortexfeed.core.context import resolve_paths, format_for_prompt


def register(app, get_model):

    @app.route('/build-prompt', methods=['POST'])
    def build_prompt():
        """
        Receives conversation + intent + files.
        Returns a ready-to-paste prompt.
        """
        data = request.json

        conversation = data.get('conversation', '')
        intent = data.get('intent', '')
        expected = data.get('expected', '')
        actual = data.get('actual', '')
        files = data.get('files', [])
        target = data.get('target', 'any AI assistant')
        project_path = data.get('project_path', '')

        # load file context
        file_context = ""
        if files:
            all_files = []
            for pat in files:
                # if project_path given, resolve relative to it
                if project_path:
                    import os
                    full = os.path.join(project_path, pat)
                    all_files.extend(resolve_paths(full))
                else:
                    all_files.extend(resolve_paths(pat))
            if all_files:
                file_context = format_for_prompt(all_files)

        # build prompt sections
        sections = []

        conversation_summary = data.get('conversation_summary', '')
        print(f"[PROMPT] conversation_summary length={len(conversation_summary)}")
        if conversation_summary:
            sections.append(f"Context from our previous conversation:\n{conversation_summary}")
        elif conversation:
            sections.append(f"Here is the conversation so far:\n\n{conversation[:1000]}")

        if intent:
            sections.append(f"I am working on the following problem:\n{intent}")

        if file_context:
            sections.append(f"Here are the relevant files:\n\n{file_context}")

        if expected:
            sections.append(f"Expected behavior:\n{expected}")

        if actual:
            sections.append(f"Current behavior / what is going wrong:\n{actual}")

        sections.append(f"Please help me. I am sending this to {target}.")

        built_prompt = "\n\n---\n\n".join(sections)

        return jsonify({
            'status': 'ok',
            'prompt': built_prompt
        })