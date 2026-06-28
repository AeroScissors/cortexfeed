# File: cortexfeed/tests/investigation/test_hypothesis_generation.py

from __future__ import annotations

from datetime import datetime, timezone

from cortexfeed.investigation.analyst.hypothesis_engine import (
    Fact,
    HypothesisEngine,
)


def _fact(statement: str) -> Fact:
    return Fact(
        id="fact-1",
        statement=statement,
        confidence=1.0,
        evidence_ids=["evidence-1"],
        source="test",
        created_at=datetime.now(timezone.utc),
    )


def test_generates_hypotheses_for_404() -> None:
    engine = HypothesisEngine()

    facts = [
        _fact(
            "GET /promise returns 404",
        )
    ]

    hypotheses = engine.generate(facts)

    statements = {
        h.statement
        for h in hypotheses
    }

    assert len(hypotheses) == 2

    assert (
        "Requested route is not registered"
        in statements
    )

    assert (
        "Request path is incorrect"
        in statements
    )


def test_generates_hypotheses_for_connection_refused() -> None:
    engine = HypothesisEngine()

    facts = [
        _fact(
            "Connection refused while calling API",
        )
    ]

    hypotheses = engine.generate(facts)

    statements = {
        h.statement
        for h in hypotheses
    }

    assert len(hypotheses) == 2

    assert (
        "Target service is not running"
        in statements
    )

    assert (
        "Network configuration issue exists"
        in statements
    )


def test_generates_hypothesis_for_timeout() -> None:
    engine = HypothesisEngine()

    facts = [
        _fact(
            "Request timeout after 30 seconds",
        )
    ]

    hypotheses = engine.generate(facts)

    statements = {
        h.statement
        for h in hypotheses
    }

    assert len(hypotheses) == 1

    assert (
        "Dependency is responding too slowly"
        in statements
    )


def test_generates_multiple_hypotheses_from_multiple_facts() -> None:
    engine = HypothesisEngine()

    facts = [
        _fact(
            "GET /promise returns 404",
        ),
        _fact(
            "Connection refused while calling API",
        ),
        _fact(
            "Request timeout after 30 seconds",
        ),
    ]

    hypotheses = engine.generate(facts)

    statements = {
        h.statement
        for h in hypotheses
    }

    assert (
        "Requested route is not registered"
        in statements
    )

    assert (
        "Request path is incorrect"
        in statements
    )

    assert (
        "Target service is not running"
        in statements
    )

    assert (
        "Network configuration issue exists"
        in statements
    )

    assert (
        "Dependency is responding too slowly"
        in statements
    )


def test_no_hypotheses_for_unrelated_fact() -> None:
    engine = HypothesisEngine()

    facts = [
        _fact(
            "Project contains one Python file",
        )
    ]

    hypotheses = engine.generate(facts)

    assert hypotheses == []