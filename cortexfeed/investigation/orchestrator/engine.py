# File: cortexfeed/investigation/orchestrator/engine.py

from __future__ import annotations

from pathlib import Path

from cortexfeed.investigation.sessions.manager import (
    SessionManager,
)
from cortexfeed.investigation.sessions.models import (
    InvestigationSession,
)

from .collector_coordinator import (
    CollectorCoordinator,
)
from .coordinator import (
    InvestigationCoordinator,
)
from .exceptions import (
    InvalidInvestigationRequestError,
    SessionResolutionError,
)
from .models import (
    InvestigationResult,
)


class InvestigationEngine:
    """
    Public entry point for CortexFeed investigations.

    Example:

        engine = InvestigationEngine(
            sessions_root=Path("data/sessions"),
            project_root=Path("."),
        )

        result = engine.investigate(
            "Continue debugging Trust Ledger"
        )
    """

    def __init__(
        self,
        *,
        sessions_root: str | Path,
        project_root: str | Path | None = None,
        file_paths: dict | None = None,
        terminal_command: str | None = None,
        terminal_stdout: str = "",
        terminal_stderr: str = "",
        terminal_exit_code: int = 0,
    ) -> None:
        self.session_manager = SessionManager(
            Path(sessions_root),
        )

        collector_coordinator = CollectorCoordinator(
            project_root=project_root,
            file_paths=file_paths,
            terminal_command=terminal_command,
            terminal_stdout=terminal_stdout,
            terminal_stderr=terminal_stderr,
            terminal_exit_code=terminal_exit_code,
        )

        self.coordinator = InvestigationCoordinator(
            session_manager=self.session_manager,
            collector_coordinator=collector_coordinator,
        )

    def investigate(
        self,
        request: str,
        *,
        project_name: str,
    ) -> InvestigationResult:
        """
        Execute a full investigation lifecycle.

        Request
            ↓
        Intent Analysis
            ↓
        Evidence Planning
            ↓
        Question Generation
            ↓
        Evidence Collection
            ↓
        Fact Extraction
            ↓
        Hypothesis Generation
            ↓
        Prompt Composition
            ↓
        Session Persistence
        """

        request = request.strip()

        if not request:
            raise InvalidInvestigationRequestError(
                "Investigation request cannot be empty."
            )

        session = self._resolve_session(
            project_name,
        )

        session.timeline.add_event(
            "user_request",
            request,
        )

        intent = self.coordinator.analyze_intent(
            request,
        )

        plan = self.coordinator.create_plan(
            intent,
        )

        self.coordinator.generate_questions(
            plan,
        )

        evidence = (
            self.coordinator.collect_evidence(
                plan,
            )
        )

        self.coordinator.analyze_evidence(
            request,
            evidence,
            session,
        )

        prompt_package = (
            self.coordinator.compose_prompt(
                session=session,
                request=request,
            )
        )

        session.timeline.add_event(
            "prompt_generated",
            f"Prompt generated for request: {request}",
        )

        self.coordinator.persist_session(
            session,
        )

        root_cause_val = None
        root_cause_conf = 0.0

        if hasattr(session, "root_cause") and session.root_cause:
            root_cause_val = session.root_cause.likely_root_cause
            root_cause_conf = session.root_cause.confidence

        return InvestigationResult(
            session=session,
            intent=intent,
            plan=plan,
            prompt_package=prompt_package,
            evidence_count=len(
                session.evidence.list()
            ),
            fact_count=session.facts.count,
            hypothesis_count=len(
                session.hypotheses.list()
            ),
            root_cause=root_cause_val,
            root_cause_confidence=root_cause_conf,
        )

    def resume(
        self,
        *,
        project_name: str,
    ) -> InvestigationSession:
        """
        Load an existing investigation session.
        """

        return self._resolve_session(
            project_name,
        )

    def session_exists(
        self,
        project_name: str,
    ) -> bool:
        return self.session_manager.session_exists(
            project_name,
        )

    def list_sessions(
        self,
    ):
        return self.session_manager.list_sessions()

    def _resolve_session(
        self,
        project_name: str,
    ) -> InvestigationSession:
        try:
            if self.session_manager.session_exists(
                project_name,
            ):
                return self.session_manager.load_session(
                    project_name,
                )

            return self.session_manager.create_session(
                project_name,
            )

        except Exception as exc:
            raise SessionResolutionError(
                f"Failed to resolve session '{project_name}'."
            ) from exc