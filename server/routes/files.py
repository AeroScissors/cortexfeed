from flask import request, jsonify
from server.ai.file_detector import detect_relevant_files, scan_project


def register(app, get_model):

    @app.route('/smart-files', methods=['POST'])
    def smart_files():
        """
        Given conversation + project path, auto-detect relevant files.
        Returns scored file list ready to attach to prompt.
        """
        data = request.json or {}
        conversation = data.get('conversation', '')
        project_path = data.get('project_path', '')
        likely_files = data.get('likely_files', [])

        if not project_path:
            return jsonify({'error': 'No project_path provided'}), 400

        detected = detect_relevant_files(
            conversation=conversation,
            project_path=project_path,
            likely_files=likely_files,
            max_results=6
        )

        return jsonify({
            'status': 'ok',
            'files': detected,
            'count': len(detected)
        })

    @app.route('/scan-project', methods=['POST'])
    def scan_project_route():
        """
        Scan a project folder and return all code files.
        Used by extension to show file tree.
        """
        data = request.json or {}
        project_path = data.get('project_path', '')

        if not project_path:
            return jsonify({'error': 'No project_path provided'}), 400

        files = scan_project(project_path)

        return jsonify({
            'status': 'ok',
            'files': files,
            'count': len(files)
        })