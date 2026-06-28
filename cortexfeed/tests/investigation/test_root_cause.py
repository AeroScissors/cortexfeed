# File: cortexfeed/tests/investigation/test_root_cause.py

from __future__ import annotations

from cortexfeed.investigation.analyst.hypothesis_engine import (
    Hypothesis,
    HypothesisStatus,
)
from cortexfeed.investigation.analyst.root_cause import (
    RootCauseAnalyzer,
)


def _hypothesis(
    statement: str,
    *,
    score: float = 0.50,
    supporting_facts: list[str] | None = None,
    contradicting_facts: list[str] | None = None,
    status: HypothesisStatus = HypothesisStatus.ACTIVE,
) -> Hypothesis:
    return Hypothesis(
        id=f"hyp-{statement}",
        statement=statement,
        score=score,
        supporting_facts=supporting_facts or [],
        contradicting_facts=contradicting_facts or [],
        status=status,
    )


def test_returns_empty_analysis_when_no_hypotheses() -> None:
    analyzer = RootCauseAnalyzer()

    result = analyzer.analyze([])

    assert result.likely_root_cause is None
    assert result.confidence == 0.0

    assert result.reasoning == [
        "No viable hypotheses available."
    ]

    assert result.alternatives == []
    assert result.candidates == []


def test_selects_highest_confidence_hypothesis() -> None:
    analyzer = RootCauseAnalyzer()

    hypotheses = [
        _hypothesis(
            "Request path is incorrect",
            score=0.40,
        ),
        _hypothesis(
            "Requested route is not registered",
            score=0.90,
        ),
        _hypothesis(
            "Network configuration issue exists",
            score=0.20,
        ),
    ]

    result = analyzer.analyze(
        hypotheses,
    )

    assert (
        result.likely_root_cause
        == "Requested route is not registered"
    )

    assert result.confidence == 0.90


def test_supporting_facts_increase_confidence() -> None:
    analyzer = RootCauseAnalyzer()

    hypotheses = [
        _hypothesis(
            "Route not registered",
            score=0.50,
            supporting_facts=[
                "404 detected",
                "route missing",
            ],
        )
    ]

    result = analyzer.analyze(
        hypotheses,
    )

    assert (
        result.likely_root_cause
        == "Route not registered"
    )

    assert result.confidence == 0.70


def test_contradicting_facts_reduce_confidence() -> None:
    analyzer = RootCauseAnalyzer()

    hypotheses = [
        _hypothesis(
            "Target service is not running",
            score=0.80,
            contradicting_facts=[
                "service healthy",
                "health check passed",
            ],
        )
    ]

    result = analyzer.analyze(
        hypotheses,
    )

    assert (
        result.likely_root_cause
        == "Target service is not running"
    )

    assert result.confidence == 0.50


def test_rejected_hypotheses_are_ignored() -> None:
    analyzer = RootCauseAnalyzer()

    hypotheses = [
        _hypothesis(
            "Rejected hypothesis",
            score=1.00,
            status=HypothesisStatus.REJECTED,
        ),
        _hypothesis(
            "Valid hypothesis",
            score=0.60,
        ),
    ]

    result = analyzer.analyze(
        hypotheses,
    )

    assert (
        result.likely_root_cause
        == "Valid hypothesis"
    )

    assert result.confidence == 0.60


def test_alternatives_are_ranked_after_winner() -> None:
    analyzer = RootCauseAnalyzer()

    hypotheses = [
        _hypothesis(
            "Winner",
            score=0.90,
        ),
        _hypothesis(
            "Alternative A",
            score=0.80,
        ),
        _hypothesis(
            "Alternative B",
            score=0.70,
        ),
    ]

    result = analyzer.analyze(
        hypotheses,
    )

    assert result.likely_root_cause == "Winner"

    assert result.alternatives == [
        "Alternative A",
        "Alternative B",
    ]


def test_reasoning_contains_support_details() -> None:
    analyzer = RootCauseAnalyzer()

    hypotheses = [
        _hypothesis(
            "Route not registered",
            score=0.60,
            supporting_facts=[
                "404 detected",
            ],
            contradicting_facts=[],
        )
    ]

    result = analyzer.analyze(
        hypotheses,
    )

    assert len(result.reasoning) == 3

    assert (
        "highest confidence score"
        in result.reasoning[0]
    )

    assert (
        "Supporting facts: 1"
        in result.reasoning[1]
    )

    assert (
        "Contradicting facts: 0"
        in result.reasoning[2]
    )