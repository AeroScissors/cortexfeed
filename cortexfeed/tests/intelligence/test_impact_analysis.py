# File: cortexfeed/tests/intelligence/test_impact_analysis.py

from cortexfeed.intelligence.capabilities.impact_analysis import (
    ImpactAnalysisCapability,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)


def _build_graph_search() -> GraphSearchV2:
    graph = Graph(
        nodes=[
            GraphNode(
                id="function:controller",
                type="FUNCTION",
                name="controller",
            ),
            GraphNode(
                id="function:login",
                type="FUNCTION",
                name="login",
            ),
            GraphNode(
                id="function:validate_user",
                type="FUNCTION",
                name="validate_user",
            ),
            GraphNode(
                id="function:create_token",
                type="FUNCTION",
                name="create_token",
            ),
        ],
        edges=[
            GraphEdge(
                source="function:controller",
                target="function:login",
                relationship="CALLS",
            ),
            GraphEdge(
                source="function:login",
                target="function:validate_user",
                relationship="CALLS",
            ),
            GraphEdge(
                source="function:validate_user",
                target="function:create_token",
                relationship="CALLS",
            ),
        ],
    )

    return GraphSearchV2(graph)


def test_symbol_found():
    capability = ImpactAnalysisCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert result.confidence > 0.0
    assert result.symbols == ["login"]


def test_symbol_missing():
    capability = ImpactAnalysisCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "missing_symbol",
    )

    assert result.confidence == 0.0
    assert "no impact information" in result.summary.lower()


def test_dependents_returned():
    capability = ImpactAnalysisCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    dependents = result.metadata.get(
        "dependents",
        [],
    )

    assert "controller" in dependents


def test_callers_returned():
    capability = ImpactAnalysisCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert "controller" in result.callers


def test_callees_returned():
    capability = ImpactAnalysisCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert "validate_user" in result.callees


def test_risk_score_computed():
    capability = ImpactAnalysisCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert result.metadata["risk_score"] > 0


def test_deterministic():
    capability = ImpactAnalysisCapability(
        _build_graph_search(),
    )

    result_a = capability.execute(
        "login",
    )

    result_b = capability.execute(
        "login",
    )

    assert result_a == result_b