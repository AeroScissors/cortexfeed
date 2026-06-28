# File: cortexfeed/investigation/analyst/fact_extractor.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable


@dataclass(slots=True)
class Evidence:
    """
    Raw investigation evidence collected from files,
    logs, terminal output, or project inspection.
    """

    id: str
    source: str
    content: str
    created_at: datetime


@dataclass(slots=True)
class Fact:
    """
    Verified observation extracted from evidence.

    Facts must remain objective and should never
    contain explanations or assumptions.
    """

    id: str
    statement: str
    confidence: float
    evidence_ids: list[str]
    source: str
    created_at: datetime


class FactExtractor:
    """
    Converts evidence into verified facts.

    The extractor intentionally stays conservative.

    It only records observations that are directly
    visible inside evidence.
    """

    # Evidence longer than this threshold is a raw document
    # or conversation dump, not a discrete fact. We skip it
    # so the fact registry stays clean and prompt-friendly.
    MAX_EVIDENCE_LENGTH = 600

    # Stored fact statements are capped here. Anything longer
    # is almost certainly not an atomic observation.
    MAX_FACT_LENGTH = 350

    def extract(self, evidence_items: Iterable[Evidence]) -> list[Fact]:
        facts: list[Fact] = []

        for evidence in evidence_items:
            extracted = self._extract_from_evidence(evidence)

            for fact in extracted:
                if not self._fact_exists(fact, facts):
                    facts.append(fact)

        return facts

    def _extract_from_evidence(self, evidence: Evidence) -> list[Fact]:
        content = evidence.content.strip()

        if not content:
            return []

        # Skip raw conversation dumps and large documents —
        # they belong in evidence, not in the facts registry.
        if len(content) > self.MAX_EVIDENCE_LENGTH:
            return []

        # Skip content that looks like a multi-turn chat log.
        if content.startswith("[USER]:") or "\n---\n" in content:
            return []

        statement = self._normalize_statement(content, self.MAX_FACT_LENGTH)

        fact = Fact(
            id=self._generate_fact_id(statement),
            statement=statement,
            confidence=1.0,
            evidence_ids=[evidence.id],
            source=evidence.source,
            created_at=datetime.now(timezone.utc),
        )

        return [fact]

    @staticmethod
    def _normalize_statement(content: str, max_length: int = 350) -> str:
        normalized = " ".join(content.split())
        if len(normalized) > max_length:
            normalized = normalized[:max_length].rstrip() + "..."
        return normalized

    @staticmethod
    def _generate_fact_id(statement: str) -> str:
        digest = sha256(statement.encode("utf-8")).hexdigest()
        return f"fact-{digest[:12]}"

    @staticmethod
    def _fact_exists(candidate: Fact, facts: list[Fact]) -> bool:
        return any(existing.id == candidate.id for existing in facts)