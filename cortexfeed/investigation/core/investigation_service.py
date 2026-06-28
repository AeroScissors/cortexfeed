# File: cortexfeed/core/investigation_service.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from cortexfeed.investigation.orchestrator.engine import (
    InvestigationEngine,
)
from cortexfeed.investigation.orchestrator.models import (
    InvestigationResult,
)
from cortexfeed.investigation.prompts.formatter import (
    PromptFormatter,
)


class InvestigationService:
    """
    High-level facade for the CortexFeed investigation system.

    Responsibilities:

    - Configure InvestigationEngine
    - Execute investigations
    - Produce formatted prompts
    - Expose simple APIs to CLI, UI, agents,
      browser extensions, and future services

    This is the integration boundary between
    CortexFeed and the investigation subsystem.
    """

    def __init__(
        self,
        *,
        sessions_root: str | Path,
        project_root: str | Path | None = None,
    ) -> None:
        self.sessions_root = Path(
            sessions_root,
        )

        self.project_root = (
            Path(project_root)
            if project_root is not None
            else None
        )

        self._formatter = PromptFormatter()

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
        """
        Execute a complete investigation.

        Example:

            result = service.investigate(
                request="Continue debugging Trust Ledger",
                project_name="trust-ledger",
            )
        """

        engine = InvestigationEngine(
            sessions_root=self.sessions_root,
            project_root=self.project_root,
            file_paths=file_paths,
            terminal_command=terminal_command,
            terminal_stdout=terminal_stdout,
            terminal_stderr=terminal_stderr,
            terminal_exit_code=terminal_exit_code,
        )

        return engine.investigate(
            request=request,
            project_name=project_name,
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
        """
        Execute an investigation and return
        a formatted prompt string.
        """

        result = self.investigate(
            request=request,
            project_name=project_name,
            file_paths=file_paths,
            terminal_command=terminal_command,
            terminal_stdout=terminal_stdout,
            terminal_stderr=terminal_stderr,
            terminal_exit_code=terminal_exit_code,
        )

        return self._formatter.format(
            result.prompt_package,
        )

    def resume(
        self,
        *,
        project_name: str,
    ):
        """
        Load an existing investigation session.
        """

        engine = InvestigationEngine(
            sessions_root=self.sessions_root,
            project_root=self.project_root,
        )

        return engine.resume(
            project_name=project_name,
        )

    def list_sessions(
        self,
    ):
        """
        Return known investigation sessions.
        """

        engine = InvestigationEngine(
            sessions_root=self.sessions_root,
            project_root=self.project_root,
        )

        return engine.list_sessions()

    def session_exists(
        self,
        project_name: str,
    ) -> bool:
        """
        Check whether a session exists.
        """

        engine = InvestigationEngine(
            sessions_root=self.sessions_root,
            project_root=self.project_root,
        )

        return engine.session_exists(
            project_name,
        )

    def summarize(
        self,
        result: InvestigationResult,
    ) -> dict[str, Any]:
        """
        Return lightweight metadata for UI,
        APIs, dashboards, and future agents.
        """

        return result.to_summary()