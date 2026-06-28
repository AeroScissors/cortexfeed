# File: cortexfeed/investigation/sessions/facts.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class VerifiedFact:
    """
    Represents a verified investigation fact.

    Facts must be evidence-backed observations.
    Assumptions and hypotheses do not belong here.
    """

    fact_id: str
    timestamp: str
    statement: str
    evidence: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        statement: str,
        evidence: list[str] | None = None,
    ) -> "VerifiedFact":
        return cls(
            fact_id=f"fact_{uuid4().hex}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            statement=statement.strip(),
            evidence=evidence or [],
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerifiedFact":
        return cls(
            fact_id=data["fact_id"],
            timestamp=data["timestamp"],
            statement=data["statement"],
            evidence=list(data.get("evidence", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FactRegistry:
    """
    Stores and persists verified facts for an investigation.

    Example:

    {
      "facts": [
        {
          "fact_id": "...",
          "statement": "GET /promise returns 404",
          "evidence": ["railway.log"]
        }
      ]
    }
    """

    FILE_NAME = "facts.json"

    def __init__(self, session_directory: Path) -> None:
        self._session_directory = session_directory
        self._facts_file = session_directory / self.FILE_NAME
        self._facts: dict[str, VerifiedFact] = {}

    @property
    def path(self) -> Path:
        return self._facts_file

    @property
    def count(self) -> int:
        return len(self._facts)

    def exists(self) -> bool:
        return self._facts_file.exists()

    def add_fact(
        self,
        statement: str,
        evidence: list[str] | None = None,
    ) -> VerifiedFact:
        normalized_statement = statement.strip()

        existing = self.find_by_statement(normalized_statement)
        if existing is not None:
            return existing

        fact = VerifiedFact.create(
            statement=normalized_statement,
            evidence=evidence,
        )

        self._facts[fact.fact_id] = fact
        return fact

    def remove_fact(self, fact_id: str) -> bool:
        if fact_id not in self._facts:
            return False

        del self._facts[fact_id]
        return True

    def get_fact(self, fact_id: str) -> VerifiedFact | None:
        return self._facts.get(fact_id)

    def find_by_statement(
        self,
        statement: str,
    ) -> VerifiedFact | None:
        normalized = statement.strip()

        for fact in self._facts.values():
            if fact.statement == normalized:
                return fact

        return None

    def list_facts(self) -> list[VerifiedFact]:
        return sorted(
            self._facts.values(),
            key=lambda fact: fact.timestamp,
        )

    def clear(self) -> None:
        self._facts.clear()

    def load(self) -> None:
        if not self._facts_file.exists():
            self._facts.clear()
            return

        with self._facts_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        self._facts = {}

        for item in payload.get("facts", []):
            fact = VerifiedFact.from_dict(item)
            self._facts[fact.fact_id] = fact

    def save(self) -> None:
        self._session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "facts": [
                fact.to_dict()
                for fact in self.list_facts()
            ]
        }

        with self._facts_file.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def delete(self) -> None:
        if self._facts_file.exists():
            self._facts_file.unlink()