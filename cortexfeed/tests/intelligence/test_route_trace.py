# File: cortexfeed/tests/intelligence/test_route_trace.py

from cortexfeed.intelligence.capabilities.route_trace import (
    RouteTraceCapability,
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
                id="route:POST:/login",
                type="ROUTE",
                name="POST:/login",
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
                source="route:POST:/login",
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


def test_route_found():
    capability = RouteTraceCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "POST",
        "/login",
    )

    assert result.confidence > 0.0
    assert result.routes == [
        "POST:/login",
    ]


def test_route_missing():
    capability = RouteTraceCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "POST",
        "/missing",
    )

    assert result.confidence == 0.0
    assert "not found" in result.summary.lower()


def test_execution_path_returned():
    capability = RouteTraceCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "POST",
        "/login",
    )

    assert "login" in result.execution_path
    assert "validate_user" in result.execution_path
    assert "create_token" in result.execution_path


def test_symbols_populated():
    capability = RouteTraceCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "POST",
        "/login",
    )

    assert result.symbols == result.execution_path


def test_metadata_correctness():
    capability = RouteTraceCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "POST",
        "/login",
    )

    assert result.metadata["route"] == "POST:/login"

    assert (
        result.metadata["path_length"]
        == len(result.execution_path)
    )


def test_deterministic():
    capability = RouteTraceCapability(
        _build_graph_search(),
    )

    result_a = capability.execute(
        "POST",
        "/login",
    )

    result_b = capability.execute(
        "POST",
        "/login",
    )

    assert result_a == result_b