# File: cortexfeed/tests/intelligence/test_repository_facade.py

from cortexfeed.intelligence.capabilities.registry import (
    CapabilityRegistry,
)
from cortexfeed.intelligence.facade import (
    RepositoryIntelligenceFacade,
)
from cortexfeed.intelligence.query_router import (
    QueryRouter,
)
from cortexfeed.intelligence.repository_service import (
    RepositoryService,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)


def _build_facade() -> RepositoryIntelligenceFacade:
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
        ],
    )

    graph_search = GraphSearchV2(
        graph,
    )

    registry = CapabilityRegistry(
        graph_search,
    )

    router = QueryRouter(
        registry,
    )

    service = RepositoryService(
        router,
    )

    return RepositoryIntelligenceFacade(
        service,
    )


def test_ask_delegates_to_service():
    facade = _build_facade()

    result = facade.ask(
        "Where is login handled?",
    )

    assert result.capability == (
        "where_is_symbol"
    )


def test_search_delegates_to_ask():
    facade = _build_facade()

    result = facade.search(
        "Where is login handled?",
    )

    assert result.capability == (
        "where_is_symbol"
    )


def test_explain_delegates_to_ask():
    facade = _build_facade()

    result = facade.explain(
        "Trace POST /login",
    )

    assert result.capability == (
        "route_trace"
    )


def test_trace_delegates_to_ask():
    facade = _build_facade()

    result = facade.trace(
        "Show login execution flow",
    )

    assert result.capability == (
        "call_chain"
    )


def test_impact_delegates_to_ask():
    facade = _build_facade()

    result = facade.impact(
        "What breaks if login changes?",
    )

    assert result.capability == (
        "impact_analysis"
    )


def test_deterministic():
    facade = _build_facade()

    result_a = facade.ask(
        "Where is login handled?",
    )

    result_b = facade.ask(
        "Where is login handled?",
    )

    assert result_a == result_b