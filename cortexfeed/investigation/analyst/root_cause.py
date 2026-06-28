# File: cortexfeed/investigation/analyst/root_cause.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .hypothesis_engine import (
    Hypothesis,
    HypothesisStatus,
)


@dataclass(slots=True)
class RootCauseCandidate:
    """
    Ranked hypothesis candidate.
    """

    hypothesis_id: str
    statement: str
    confidence: float
    supporting_facts: int
    contradicting_facts: int


@dataclass(slots=True)
class RootCauseAnalysis:
    """
    Final root cause assessment.

    This does not create hypotheses.
    It only evaluates existing ones.
    """

    likely_root_cause: str | None
    confidence: float
    alternatives: list[str] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    candidates: list[RootCauseCandidate] = field(
        default_factory=list
    )


class RootCauseAnalyzer:
    """
    Evaluates hypotheses and determines
    the most likely root cause.

    Facts and hypotheses remain separate.

    This component never creates facts
    and never creates hypotheses.
    """

    def analyze(
        self,
        hypotheses: Iterable[Hypothesis],
    ) -> RootCauseAnalysis:
        ranked_candidates = self._rank_hypotheses(
            hypotheses
        )

        if not ranked_candidates:
            return RootCauseAnalysis(
                likely_root_cause=None,
                confidence=0.0,
                reasoning=[
                    "No viable hypotheses available."
                ],
            )

        best_candidate = ranked_candidates[0]

        alternatives = [
            candidate.statement
            for candidate in ranked_candidates[1:]
        ]

        reasoning = [
            (
                f"Hypothesis '{best_candidate.statement}' "
                f"has the highest confidence score "
                f"({best_candidate.confidence:.2f})."
            ),
            (
                f"Supporting facts: "
                f"{best_candidate.supporting_facts}"
            ),
            (
                f"Contradicting facts: "
                f"{best_candidate.contradicting_facts}"
            ),
        ]

        return RootCauseAnalysis(
            likely_root_cause=best_candidate.statement,
            confidence=best_candidate.confidence,
            alternatives=alternatives,
            reasoning=reasoning,
            candidates=ranked_candidates,
        )

    def _rank_hypotheses(
        self,
        hypotheses: Iterable[Hypothesis],
    ) -> list[RootCauseCandidate]:
        candidates: list[
            RootCauseCandidate
        ] = []

        for hypothesis in hypotheses:
            if (
                hypothesis.status
                == HypothesisStatus.REJECTED
            ):
                continue

            confidence = self._calculate_confidence(
                hypothesis
            )

            candidates.append(
                RootCauseCandidate(
                    hypothesis_id=hypothesis.id,
                    statement=hypothesis.statement,
                    confidence=confidence,
                    supporting_facts=len(
                        hypothesis.supporting_facts
                    ),
                    contradicting_facts=len(
                        hypothesis.contradicting_facts
                    ),
                )
            )

        candidates.sort(
            key=lambda candidate: candidate.confidence,
            reverse=True,
        )

        return candidates

    @staticmethod
    def _calculate_confidence(
        hypothesis: Hypothesis,
    ) -> float:
        support_count = len(
            hypothesis.supporting_facts
        )

        contradiction_count = len(
            hypothesis.contradicting_facts
        )

        score = hypothesis.score

        score += support_count * 0.10
        score -= contradiction_count * 0.15

        if score < 0.0:
            return 0.0

        if score > 1.0:
            return 1.0

        return round(score, 2)