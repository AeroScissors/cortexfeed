# File: cortexfeed/tests/intelligence/test_query_router.py

from cortexfeed.intelligence.capabilities.registry import (
    CapabilityRegistry,
)
from cortexfeed.intelligence.query_router import (
    QueryRouter,
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
                source="route:POST:/login",
                target="function:login",
                relationship="CALLS",
            ),
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


def _build_router() -> QueryRouter:
    graph_search = _build_graph_search()

    registry = CapabilityRegistry(
        graph_search,
    )

    return QueryRouter(
        registry,
    )


def test_where_is_login_handled():
    router = _build_router()

    result = router.route(
        "Where is login handled?",
    )

    assert result.capability == "where_is_symbol"
    assert result.confidence > 0.0
    assert "login" in result.symbols


def test_trace_post_login_route():
    router = _build_router()

    result = router.route(
        "Trace POST /login",
    )

    assert result.capability == "route_trace"
    assert result.confidence > 0.0
    assert "POST:/login" in result.routes


def test_impact_analysis_query():
    router = _build_router()

    result = router.route(
        "What breaks if login changes?",
    )

    assert result.capability == "impact_analysis"
    assert result.confidence > 0.0


def test_call_chain_query():
    router = _build_router()

    result = router.route(
        "Show login execution flow",
    )

    assert result.capability == "call_chain"
    assert result.confidence > 0.0
    assert "login" in result.execution_path


def test_unknown_query():
    router = _build_router()

    result = router.route(
        "authentication architecture",
    )

    assert result.capability == "unknown"
    assert result.confidence == 0.0


def test_empty_query():
    router = _build_router()

    result = router.route(
        "",
    )

    assert result.capability == "none"
    assert result.confidence == 0.0


def test_deterministic_routing():
    router = _build_router()

    result_a = router.route(
        "Where is login handled?",
    )

    result_b = router.route(
        "Where is login handled?",
    )

    assert result_a == result_b


def test_route_query_case_insensitive():
    router = _build_router()

    result = router.route(
        "trace post /login",
    )

    assert result.capability == "route_trace"


def test_symbol_query_case_insensitive():
    router = _build_router()

    result = router.route(
        "where is login handled",
    )

    assert result.capability == "where_is_symbol"


def test_call_chain_preserves_execution_path():
    router = _build_router()

    result = router.route(
        "Show login execution flow",
    )

    assert result.execution_path == [
        "login",
        "validate_user",
        "create_token",
    ]