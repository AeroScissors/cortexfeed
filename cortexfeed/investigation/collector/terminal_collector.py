# File: cortexfeed/investigation/collector/terminal_collector.py

from __future__ import annotations

from datetime import datetime, timezone

from .base import BaseCollector
from .models import Evidence, EvidenceType


class TerminalCollector(BaseCollector):
    """
    Collects terminal execution evidence.

    Responsibilities:
    - Capture stdout
    - Capture stderr
    - Capture exit code
    - Preserve command metadata
    """

    def __init__(
        self,
        *,
        command: str,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        duration_seconds: float | None = None,
    ) -> None:
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.duration_seconds = duration_seconds

    def collect(self) -> list[Evidence]:
        content = self._build_content()

        evidence = Evidence.create(
            evidence_type=EvidenceType.TERMINAL,
            source="terminal_collector",
            path=None,
            content=content,
            metadata={
                "command": self.command,
                "exit_code": self.exit_code,
                "duration_seconds": self.duration_seconds,
                "stdout_length": len(self.stdout),
                "stderr_length": len(self.stderr),
                "has_errors": bool(self.stderr.strip()),
                "captured_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
        )

        return [evidence]

    def _build_content(self) -> str:
        sections: list[str] = [
            f"COMMAND: {self.command}",
            f"EXIT CODE: {self.exit_code}",
            "",
            "================ STDOUT ================",
            self.stdout.strip(),
            "",
            "================ STDERR ================",
            self.stderr.strip(),
        ]

        return "\n".join(sections)