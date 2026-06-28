# File: cortexfeed/investigation/sessions/memory.py

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class InvestigationMemory:
    """
    Durable investigation memory persisted across sessions.

    Stores only long-lived investigation knowledge that should survive
    between runs.
    """

    known_files: set[str] = field(default_factory=set)
    known_errors: set[str] = field(default_factory=set)
    known_decisions: set[str] = field(default_factory=set)
    known_facts: set[str] = field(default_factory=set)
    known_hypotheses: set[str] = field(default_factory=set)

    def add_file(self, file_path: str) -> None:
        self.known_files.add(file_path)

    def add_error(self, error: str) -> None:
        self.known_errors.add(error)

    def add_decision(self, decision: str) -> None:
        self.known_decisions.add(decision)

    def add_fact(self, fact: str) -> None:
        self.known_facts.add(fact)

    def add_hypothesis(self, hypothesis: str) -> None:
        self.known_hypotheses.add(hypothesis)

    def clear(self) -> None:
        self.known_files.clear()
        self.known_errors.clear()
        self.known_decisions.clear()
        self.known_facts.clear()
        self.known_hypotheses.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "known_files": sorted(self.known_files),
            "known_errors": sorted(self.known_errors),
            "known_decisions": sorted(self.known_decisions),
            "known_facts": sorted(self.known_facts),
            "known_hypotheses": sorted(self.known_hypotheses),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvestigationMemory":
        return cls(
            known_files=set(data.get("known_files", [])),
            known_errors=set(data.get("known_errors", [])),
            known_decisions=set(data.get("known_decisions", [])),
            known_facts=set(data.get("known_facts", [])),
            known_hypotheses=set(data.get("known_hypotheses", [])),
        )


class MemoryStore:
    """
    JSON persistence layer for InvestigationMemory.

    Example:
        session_dir/
            memory.json
    """

    FILE_NAME = "memory.json"

    def __init__(self, session_directory: Path) -> None:
        self._session_directory = session_directory
        self._memory_file = session_directory / self.FILE_NAME

    @property
    def path(self) -> Path:
        return self._memory_file

    def exists(self) -> bool:
        return self._memory_file.exists()

    def load(self) -> InvestigationMemory:
        if not self._memory_file.exists():
            return InvestigationMemory()

        with self._memory_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return InvestigationMemory.from_dict(data)

    def save(self, memory: InvestigationMemory) -> None:
        self._session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._memory_file.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            json.dump(
                memory.to_dict(),
                file,
                indent=2,
                ensure_ascii=False,
            )

    def delete(self) -> None:
        if self._memory_file.exists():
            self._memory_file.unlink()