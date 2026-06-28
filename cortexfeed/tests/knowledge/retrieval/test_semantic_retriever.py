# File: cortexfeed/tests/knowledge/retrieval/test_semantic_retriever.py

from cortexfeed.intelligence.repository_intent import (
    RepositoryIntent,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)
from cortexfeed.knowledge.retrieval.semantic_retriever import (
    SemanticRetriever,
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


def test_route_retrieval():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="bug_investigation",
        confidence=1.0,
        routes=["POST:/login"],
        raw_query="POST /login returns 500",
    )

    result = retriever.retrieve(intent)

    assert "POST:/login" in result["routes"]
    assert "login" in result["symbols"]
    assert "validate_user" in result["symbols"]
    assert "create_token" in result["symbols"]


def test_symbol_lookup():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="symbol_lookup",
        confidence=1.0,
        raw_query="login",
    )

    result = retriever.retrieve(intent)

    assert "login" in result["symbols"]


def test_unknown_symbol():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="symbol_lookup",
        confidence=1.0,
        raw_query="unknown_symbol",
    )

    result = retriever.retrieve(intent)

    assert result["symbols"] == []
    assert result["routes"] == []
    assert result["files"] == []


def test_deduplicates_symbols():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="symbol_lookup",
        confidence=1.0,
        routes=["POST:/login"],
        raw_query="login",
    )

    result = retriever.retrieve(intent)

    assert len(result["symbols"]) == len(
        set(result["symbols"])
    )


def test_deduplicates_routes():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="bug_investigation",
        confidence=1.0,
        routes=[
            "POST:/login",
            "POST:/login",
        ],
        raw_query="POST /login returns 500",
    )

    result = retriever.retrieve(intent)

    assert result["routes"] == [
        "POST:/login"
    ]


def test_empty_intent():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="general_search",
        confidence=0.0,
        raw_query="",
    )

    result = retriever.retrieve(intent)

    assert result == {
        "symbols": [],
        "routes": [],
        "files": [],
    }


def test_route_trace_is_expanded():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="bug_investigation",
        confidence=1.0,
        routes=["POST:/login"],
        raw_query="POST /login",
    )

    result = retriever.retrieve(intent)

    assert "login" in result["symbols"]
    assert "validate_user" in result["symbols"]
    assert "create_token" in result["symbols"]


def test_retrieval_is_deterministic():
    retriever = SemanticRetriever(
        _build_graph_search(),
    )

    intent = RepositoryIntent(
        intent="symbol_lookup",
        confidence=1.0,
        raw_query="login",
    )

    result_a = retriever.retrieve(intent)
    result_b = retriever.retrieve(intent)

    assert result_a == result_b