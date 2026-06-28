# File: cortexfeed/investigation/facade.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from cortexfeed.investigation.core.investigation_service import (
    InvestigationService,
)
from cortexfeed.investigation.orchestrator.models import (
    InvestigationResult,
)
from cortexfeed.investigation.sessions.models import (
    InvestigationSession,
)


class CortexFeedInvestigation:
    """
    High-level investigation facade.

    This is intended to be the primary integration
    surface for the rest of CortexFeed.

    Future integrations:

    - CLI
    - Desktop UI
    - Browser Extension
    - Repository Intelligence
    - Semantic Retrieval
    - Multi-Agent Runtime
    """

    def __init__(
        self,
        *,
        sessions_root: str | Path,
        project_root: str | Path | None = None,
    ) -> None:
        self._service = InvestigationService(
            sessions_root=sessions_root,
            project_root=project_root,
        )

    def investigate(
        self,
        *,
        request: str,
        project_name: str,
        file_paths: dict | None = None,
        terminal_command: str | None = None,
        terminal_stdout: str = "",
        terminal_stderr: str = "",
        terminal_exit_code: int = 0,
    ) -> InvestigationResult:
        return self._service.investigate(
            request=request,
            project_name=project_name,
            file_paths=file_paths,
            terminal_command=terminal_command,
            terminal_stdout=terminal_stdout,
            terminal_stderr=terminal_stderr,
            terminal_exit_code=terminal_exit_code,
        )

    def generate_prompt(
        self,
        *,
        request: str,
        project_name: str,
        file_paths: dict | None = None,
        terminal_command: str | None = None,
        terminal_stdout: str = "",
        terminal_stderr: str = "",
        terminal_exit_code: int = 0,
    ) -> str:
        return self._service.generate_prompt(
            request=request,
            project_name=project_name,
            file_paths=file_paths,
            terminal_command=terminal_command,
            terminal_stdout=terminal_stdout,
            terminal_stderr=terminal_stderr,
            terminal_exit_code=terminal_exit_code,
        )

    def resume(
        self,
        *,
        project_name: str,
    ) -> InvestigationSession:
        return self._service.resume(
            project_name=project_name,
        )

    def list_sessions(
        self,
    ):
        return self._service.list_sessions()

    def session_exists(
        self,
        project_name: str,
    ) -> bool:
        return self._service.session_exists(
            project_name,
        )

    def summarize(
        self,
        result: InvestigationResult,
    ) -> dict[str, Any]:
        return self._service.summarize(
            result,
        )