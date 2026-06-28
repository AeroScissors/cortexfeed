# File: cortexfeed/api/investigate_api.py

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify, request

from cortexfeed.config.paths import ensure_data_dirs
from cortexfeed.config.settings import INVESTIGATION_SESSIONS_ROOT
from cortexfeed.investigation.orchestrator.engine import InvestigationEngine
from cortexfeed.investigation.planner.models import EvidenceType
from cortexfeed.investigation.prompts.formatter import PromptFormatter

investigate_bp = Blueprint("investigate", __name__)

_formatter = PromptFormatter()


def _build_file_paths(data: dict) -> dict:
    """
    Expect payload shape:
    {
      "file_paths": {
        "server_logs": "/abs/path/server.log",
        "stack_trace": "/abs/path/trace.log",
        ...
      }
    }
    Maps string keys to EvidenceType enum values.
    """
    raw = data.get("file_paths") or {}
    mapping = {e.value: e for e in EvidenceType}
    result = {}
    for key, path_str in raw.items():
        evidence_type = mapping.get(key)
        if evidence_type and path_str:
            p = Path(path_str)
            if p.exists():
                result[evidence_type] = p
    return result


@investigate_bp.route("/investigate", methods=["POST"])
def investigate():
    """
    Run a full investigation.

    Body:
    {
      "request":              "Debug missing route",
      "project_name":         "trust-ledger",
      "project_root":         "/optional/path",
      "file_paths":           { "server_logs": "...", "stack_trace": "..." },
      "terminal_command":     "python app.py",
      "terminal_stdout":      "...",
      "terminal_stderr":      "...",
      "terminal_exit_code":   1
    }
    """
    ensure_data_dirs()
    data = request.json or {}

    investigation_request = data.get("request", "").strip()
    project_name = data.get("project_name", "").strip()

    if not investigation_request:
        return jsonify({"error": "request is required"}), 400
    if not project_name:
        return jsonify({"error": "project_name is required"}), 400

    project_root_raw = data.get("project_root")
    project_root = Path(project_root_raw) if project_root_raw else None

    file_paths = _build_file_paths(data)

    terminal_command = data.get("terminal_command") or None
    terminal_stdout = data.get("terminal_stdout", "")
    terminal_stderr = data.get("terminal_stderr", "")
    terminal_exit_code = int(data.get("terminal_exit_code", 0))

    try:
        engine = InvestigationEngine(
            sessions_root=INVESTIGATION_SESSIONS_ROOT,
            project_root=project_root,
            file_paths=file_paths or None,
            terminal_command=terminal_command,
            terminal_stdout=terminal_stdout,
            terminal_stderr=terminal_stderr,
            terminal_exit_code=terminal_exit_code,
        )

        result = engine.investigate(
            request=investigation_request,
            project_name=project_name,
        )

        formatted_prompt = _formatter.format(result.prompt_package)

        return jsonify({
            "status": "ok",
            "summary": result.to_summary(),
            "prompt": formatted_prompt,
            "facts": [
                f.statement
                for f in result.session.facts.list_facts()
            ],
            "hypotheses": [
                {"statement": h.statement, "status": h.status}
                for h in result.session.hypotheses.list()
            ],
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@investigate_bp.route("/investigate/prompt", methods=["POST"])
def generate_prompt():
    """
    Run investigation and return only the formatted prompt string.
    Same body as /investigate.
    """
    ensure_data_dirs()
    data = request.json or {}

    investigation_request = data.get("request", "").strip()
    project_name = data.get("project_name", "").strip()

    if not investigation_request:
        return jsonify({"error": "request is required"}), 400
    if not project_name:
        return jsonify({"error": "project_name is required"}), 400

    project_root_raw = data.get("project_root")
    project_root = Path(project_root_raw) if project_root_raw else None
    file_paths = _build_file_paths(data)
    terminal_command = data.get("terminal_command") or None

    try:
        engine = InvestigationEngine(
            sessions_root=INVESTIGATION_SESSIONS_ROOT,
            project_root=project_root,
            file_paths=file_paths or None,
            terminal_command=terminal_command,
            terminal_stdout=data.get("terminal_stdout", ""),
            terminal_stderr=data.get("terminal_stderr", ""),
            terminal_exit_code=int(data.get("terminal_exit_code", 0)),
        )

        result = engine.investigate(
            request=investigation_request,
            project_name=project_name,
        )

        return jsonify({
            "status": "ok",
            "prompt": _formatter.format(result.prompt_package),
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500