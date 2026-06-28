# File: cortexfeed/investigation/analyst/hypothesis_engine.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable


@dataclass(slots=True)
class Fact:
    """
    Minimal fact contract used by the hypothesis engine.
    """

    id: str
    statement: str
    confidence: float
    evidence_ids: list[str]
    source: str
    created_at: object


class HypothesisStatus(str, Enum):
    ACTIVE = "active"
    SUPPORTED = "supported"
    REJECTED = "rejected"


@dataclass(slots=True)
class Hypothesis:
    """
    Possible explanation for one or more facts.

    Hypotheses are not facts.
    """

    id: str
    statement: str
    supporting_facts: list[str]
    contradicting_facts: list[str]
    score: float
    status: HypothesisStatus


class HypothesisEngine:
    """
    Generates and evaluates hypotheses.

    This initial implementation is rule-based and
    deterministic. No AI inference occurs here.
    """

    def generate(self, facts: Iterable[Fact]) -> list[Hypothesis]:
        fact_list = list(facts)

        hypotheses: list[Hypothesis] = []

        for fact in fact_list:
            hypotheses.extend(
                self._generate_from_fact(fact)
            )

        return self._deduplicate(hypotheses)

    def update_status(
        self,
        hypotheses: list[Hypothesis],
    ) -> list[Hypothesis]:
        for hypothesis in hypotheses:
            support_count = len(hypothesis.supporting_facts)
            contradiction_count = len(
                hypothesis.contradicting_facts
            )

            if contradiction_count > support_count:
                hypothesis.status = HypothesisStatus.REJECTED
                hypothesis.score = 0.0

            elif support_count >= 2:
                hypothesis.status = HypothesisStatus.SUPPORTED
                hypothesis.score = min(
                    1.0,
                    0.5 + (support_count * 0.1),
                )

            else:
                hypothesis.status = HypothesisStatus.ACTIVE
                hypothesis.score = 0.5

        return hypotheses

    def _generate_from_fact(
        self,
        fact: Fact,
    ) -> list[Hypothesis]:
        statement = fact.statement.lower()

        generated: list[Hypothesis] = []

        if "404" in statement:
            generated.append(
                self._create_hypothesis(
                    statement="Requested route is not registered",
                    supporting_fact_id=fact.id,
                )
            )

            generated.append(
                self._create_hypothesis(
                    statement="Request path is incorrect",
                    supporting_fact_id=fact.id,
                )
            )

        if "connection refused" in statement:
            generated.append(
                self._create_hypothesis(
                    statement="Target service is not running",
                    supporting_fact_id=fact.id,
                )
            )

            generated.append(
                self._create_hypothesis(
                    statement="Network configuration issue exists",
                    supporting_fact_id=fact.id,
                )
            )

        if "timeout" in statement:
            generated.append(
                self._create_hypothesis(
                    statement="Dependency is responding too slowly",
                    supporting_fact_id=fact.id,
                )
            )

        return generated

    def _create_hypothesis(
        self,
        statement: str,
        supporting_fact_id: str,
    ) -> Hypothesis:
        return Hypothesis(
            id=self._generate_hypothesis_id(statement),
            statement=statement,
            supporting_facts=[supporting_fact_id],
            contradicting_facts=[],
            score=0.5,
            status=HypothesisStatus.ACTIVE,
        )

    @staticmethod
    def _generate_hypothesis_id(
        statement: str,
    ) -> str:
        digest = sha256(
            statement.encode("utf-8")
        ).hexdigest()

        return f"hyp-{digest[:12]}"

    @staticmethod
    def _deduplicate(
        hypotheses: list[Hypothesis],
    ) -> list[Hypothesis]:
        unique: dict[str, Hypothesis] = {}

        for hypothesis in hypotheses:
            existing = unique.get(hypothesis.id)

            if existing is None:
                unique[hypothesis.id] = hypothesis
                continue

            existing.supporting_facts.extend(
                hypothesis.supporting_facts
            )

        return list(unique.values())