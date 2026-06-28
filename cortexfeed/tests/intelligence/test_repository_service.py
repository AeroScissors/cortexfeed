# File: cortexfeed/tests/intelligence/test_repository_service.py

from cortexfeed.intelligence.capabilities.registry import (
    CapabilityRegistry,
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


def _build_service() -> RepositoryService:
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

    graph_search = GraphSearchV2(
        graph,
    )

    registry = CapabilityRegistry(
        graph_search,
    )

    router = QueryRouter(
        registry,
    )

    return RepositoryService(
        router,
    )


def test_symbol_lookup_request():
    service = _build_service()

    result = service.answer(
        "Where is login handled?",
    )

    assert result.capability == "where_is_symbol"
    assert result.confidence > 0.0
    assert "login" in result.answer.lower()


def test_route_trace_request():
    service = _build_service()

    result = service.answer(
        "Trace POST /login",
    )

    assert result.capability == "route_trace"
    assert result.confidence > 0.0
    assert "Execution Path" in result.answer


def test_impact_analysis_request():
    service = _build_service()

    result = service.answer(
        "What breaks if login changes?",
    )

    assert result.capability == "impact_analysis"
    assert result.confidence > 0.0


def test_call_chain_request():
    service = _build_service()

    result = service.answer(
        "Show login execution flow",
    )

    assert result.capability == "call_chain"
    assert result.confidence > 0.0
    assert "Call Chain" in result.answer


def test_unknown_query():
    service = _build_service()

    result = service.answer(
        "authentication architecture",
    )

    assert result.capability == "unknown"
    assert result.confidence == 0.0


def test_empty_query():
    service = _build_service()

    result = service.answer(
        "",
    )

    assert result.capability == "none"
    assert result.confidence == 0.0


def test_evidence_extraction():
    service = _build_service()

    result = service.answer(
        "Where is login handled?",
    )

    assert "login" in result.evidence
    assert "controller" in result.evidence
    assert "validate_user" in result.evidence


def test_deterministic_answers():
    service = _build_service()

    result_a = service.answer(
        "Where is login handled?",
    )

    result_b = service.answer(
        "Where is login handled?",
    )

    assert result_a == result_b