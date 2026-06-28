# File: cortexfeed/investigation/collector/log_collector.py

from __future__ import annotations

from pathlib import Path

from .base import PathCollector
from .models import Evidence, EvidenceType


class LogCollector(PathCollector):
    """
    Collects log evidence while preserving chronology.

    Responsibilities:
    - Read logs
    - Preserve ordering
    - Trim oversized logs
    - Retain recent diagnostic context
    """

    def __init__(
        self,
        path: str | Path,
        *,
        max_lines: int = 5000,
        head_lines: int = 500,
        tail_lines: int = 2000,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(path)

        self.max_lines = max_lines
        self.head_lines = head_lines
        self.tail_lines = tail_lines
        self.encoding = encoding

    def collect(self) -> list[Evidence]:
        if not self.exists:
            raise FileNotFoundError(self.path)

        if not self.is_file:
            raise ValueError(f"Expected log file, got: {self.path}")

        lines = self._read_lines()

        original_line_count = len(lines)

        trimmed_lines = self._trim_lines(lines)

        content = "\n".join(trimmed_lines)

        evidence = Evidence.create(
            evidence_type=EvidenceType.LOG,
            source="log_collector",
            path=str(self.path),
            content=content,
            metadata={
                "filename": self.path.name,
                "size_bytes": self.path.stat().st_size,
                "original_line_count": original_line_count,
                "retained_line_count": len(trimmed_lines),
                "was_trimmed": original_line_count > len(trimmed_lines),
            },
        )

        return [evidence]

    def _read_lines(self) -> list[str]:
        with self.path.open(
            mode="r",
            encoding=self.encoding,
            errors="replace",
        ) as file_handle:
            return file_handle.read().splitlines()

    def _trim_lines(self, lines: list[str]) -> list[str]:
        if len(lines) <= self.max_lines:
            return lines

        head = lines[: self.head_lines]
        tail = lines[-self.tail_lines :]

        marker = [
            "",
            "================ TRIMMED LOG ================",
            f"{len(lines) - len(head) - len(tail)} lines omitted",
            "Chronology preserved:",
            "- beginning retained",
            "- ending retained",
            "=============================================",
            "",
        ]

        return head + marker + tail