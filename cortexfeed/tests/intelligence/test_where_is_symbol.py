# File: cortexfeed/tests/intelligence/test_where_is_symbol.py

from cortexfeed.intelligence.capabilities.where_is_symbol import (
    WhereIsSymbolCapability,
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
        ],
    )

    return GraphSearchV2(graph)


def test_symbol_found():
    capability = WhereIsSymbolCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert result.confidence > 0.0
    assert result.symbols == ["login"]
    assert "login" in result.summary


def test_symbol_missing():
    capability = WhereIsSymbolCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "missing_symbol",
    )

    assert result.confidence == 0.0
    assert "not found" in result.summary.lower()


def test_callers_returned():
    capability = WhereIsSymbolCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert "controller" in result.callers


def test_callees_returned():
    capability = WhereIsSymbolCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert "validate_user" in result.callees


def test_metadata_returned():
    capability = WhereIsSymbolCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert result.metadata["node_id"] == "function:login"
    assert result.metadata["node_type"] == "FUNCTION"


def test_deterministic():
    capability = WhereIsSymbolCapability(
        _build_graph_search(),
    )

    result_a = capability.execute(
        "login",
    )

    result_b = capability.execute(
        "login",
    )

    assert result_a == result_b