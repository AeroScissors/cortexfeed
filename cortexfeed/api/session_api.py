# File: cortexfeed/api/session_api.py

from __future__ import annotations

from flask import Blueprint, jsonify, request

from cortexfeed.config.paths import ensure_data_dirs
from cortexfeed.config.settings import INVESTIGATION_SESSIONS_ROOT
from cortexfeed.investigation.orchestrator.engine import InvestigationEngine

session_bp = Blueprint("session", __name__)


@session_bp.route("/sessions", methods=["GET"])
def list_sessions():
    ensure_data_dirs()
    engine = InvestigationEngine(sessions_root=INVESTIGATION_SESSIONS_ROOT)
    sessions = engine.list_sessions()
    return jsonify({
        "status": "ok",
        "sessions": [
            {
                "project_name": s.project_name,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in sessions
        ],
    })


@session_bp.route("/sessions/<project_name>", methods=["GET"])
def get_session(project_name: str):
    ensure_data_dirs()
    engine = InvestigationEngine(sessions_root=INVESTIGATION_SESSIONS_ROOT)

    if not engine.session_exists(project_name):
        return jsonify({"error": f"Session not found: {project_name}"}), 404

    try:
        session = engine.resume(project_name=project_name)
        stats = engine.session_manager.get_session_stats(session)
        return jsonify({
            "status": "ok",
            "project_name": project_name,
            "stats": stats,
            "facts": [f.statement for f in session.facts.list_facts()],
            "hypotheses": [
                {"statement": h.statement, "status": h.status}
                for h in session.hypotheses.list()
            ],
            "timeline": [
                {"event_type": e.event_type, "content": e.content, "timestamp": e.timestamp}
                for e in session.timeline.list_events()
            ],
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@session_bp.route("/sessions/<project_name>", methods=["DELETE"])
def delete_session(project_name: str):
    ensure_data_dirs()
    from cortexfeed.investigation.sessions.manager import SessionManager
    manager = SessionManager(INVESTIGATION_SESSIONS_ROOT)

    if not manager.session_exists(project_name):
        return jsonify({"error": f"Session not found: {project_name}"}), 404

    try:
        manager.delete_session(project_name)
        return jsonify({"status": "ok", "deleted": project_name})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500