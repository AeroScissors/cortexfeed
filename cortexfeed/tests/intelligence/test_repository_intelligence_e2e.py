# File: cortexfeed/tests/intelligence/test_repository_intelligence_e2e.py

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


def test_symbol_lookup_end_to_end():
    service = _build_service()

    result = service.answer(
        "Where is login handled?",
    )

    assert result.capability == "where_is_symbol"
    assert result.confidence > 0.0

    assert "login" in result.answer.lower()
    assert "controller" in result.answer
    assert "validate_user" in result.answer

    assert "login" in result.evidence
    assert "controller" in result.evidence
    assert "validate_user" in result.evidence


def test_route_trace_end_to_end():
    service = _build_service()

    result = service.answer(
        "Trace POST /login",
    )

    assert result.capability == "route_trace"
    assert result.confidence > 0.0

    assert "Execution Path" in result.answer

    assert "login" in result.evidence
    assert "validate_user" in result.evidence
    assert "create_token" in result.evidence

    assert result.metadata["route"] == "POST:/login"


def test_impact_analysis_end_to_end():
    service = _build_service()

    result = service.answer(
        "What breaks if login changes?",
    )

    assert result.capability == "impact_analysis"
    assert result.confidence > 0.0

    assert "affects" in result.answer.lower()

    assert "controller" in (
        result.metadata.get(
            "dependents",
            [],
        )
    )

    assert (
        result.metadata["risk_score"]
        > 0
    )


def test_call_chain_end_to_end():
    service = _build_service()

    result = service.answer(
        "Show login execution flow",
    )

    assert result.capability == "call_chain"
    assert result.confidence > 0.0

    assert "Call Chain" in result.answer

    assert result.evidence == [
        "create_token",
        "login",
        "validate_user",
    ]


def test_metadata_survives_pipeline():
    service = _build_service()

    result = service.answer(
        "Trace POST /login",
    )

    assert "route" in result.metadata
    assert "path_length" in result.metadata


def test_deterministic_execution():
    service = _build_service()

    result_a = service.answer(
        "Where is login handled?",
    )

    result_b = service.answer(
        "Where is login handled?",
    )

    assert result_a == result_b