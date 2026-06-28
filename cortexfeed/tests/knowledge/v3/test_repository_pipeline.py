# File: cortexfeed/tests/knowledge/v3/test_repository_pipeline.py

from cortexfeed.knowledge.context.context_builder import (
    KnowledgeContextBuilder,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)
from cortexfeed.knowledge.ranking.v2.evidence_selector_v2 import (
    EvidenceSelectorV2,
)


class FakeRelevanceScorer:
    def score(self, issue: str):
        return {
            "files": [
                {
                    "name": "auth/service.py",
                    "score": 0.95,
                }
            ],
            "symbols": [
                {
                    "name": "login",
                    "score": 1.0,
                }
            ],
            "routes": [
                {
                    "name": "POST:/login",
                    "score": 1.0,
                }
            ],
        }


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
            GraphNode(
                id="symbol:DATABASE_URL",
                type="EXTERNAL_SYMBOL",
                name="DATABASE_URL",
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
            GraphEdge(
                source="function:login",
                target="symbol:DATABASE_URL",
                relationship="REFERENCES",
            ),
        ],
    )

    return GraphSearchV2(graph)


def test_repository_pipeline_end_to_end():
    graph_search = _build_graph_search()

    selector = EvidenceSelectorV2(
        graph_search=graph_search,
        relevance_scorer=FakeRelevanceScorer(),
    )

    builder = KnowledgeContextBuilder(
        graph_search=graph_search,
    )

    evidence = selector.select(
        "POST /login returns 500",
    )

    context = builder.build(
        issue="POST /login returns 500",
        evidence=evidence,
    )

    assert context.issue == "POST /login returns 500"

    assert "auth/service.py" in context.files

    symbol_names = {
        symbol.name
        for symbol in context.symbols
    }

    assert "login" in symbol_names

    dependency_pairs = {
        (
            dep.source,
            dep.target,
        )
        for dep in context.dependencies
    }

    assert (
        "login",
        "DATABASE_URL",
    ) in dependency_pairs

    assert "controller" in context.callers

    assert "validate_user" in context.callees

    assert "POST:/login" in context.routes

    assert len(context.call_chains) > 0


def test_repository_pipeline_route_expansion():
    graph_search = _build_graph_search()

    selector = EvidenceSelectorV2(
        graph_search=graph_search,
        relevance_scorer=FakeRelevanceScorer(),
    )

    builder = KnowledgeContextBuilder(
        graph_search=graph_search,
    )

    evidence = selector.select(
        "POST /login fails",
    )

    context = builder.build(
        issue="POST /login fails",
        evidence=evidence,
    )

    route_chains = [
        chain
        for chain in context.call_chains
        if chain[0].startswith("Route(")
    ]

    assert len(route_chains) == 1

    chain = route_chains[0]

    assert "login" in chain
    assert "validate_user" in chain
    assert "create_token" in chain


def test_repository_pipeline_caller_callee_expansion():
    graph_search = _build_graph_search()

    selector = EvidenceSelectorV2(
        graph_search=graph_search,
        relevance_scorer=FakeRelevanceScorer(),
    )

    builder = KnowledgeContextBuilder(
        graph_search=graph_search,
    )

    evidence = selector.select(
        "authentication issue",
    )

    context = builder.build(
        issue="authentication issue",
        evidence=evidence,
    )

    assert "controller" in context.callers
    assert "validate_user" in context.callees


def test_repository_pipeline_is_deterministic():
    graph_search = _build_graph_search()

    selector = EvidenceSelectorV2(
        graph_search=graph_search,
        relevance_scorer=FakeRelevanceScorer(),
    )

    builder = KnowledgeContextBuilder(
        graph_search=graph_search,
    )

    evidence_a = selector.select(
        "POST /login returns 500",
    )

    context_a = builder.build(
        issue="POST /login returns 500",
        evidence=evidence_a,
    )

    evidence_b = selector.select(
        "POST /login returns 500",
    )

    context_b = builder.build(
        issue="POST /login returns 500",
        evidence=evidence_b,
    )

    assert context_a.files == context_b.files
    assert context_a.routes == context_b.routes
    assert context_a.callers == context_b.callers
    assert context_a.callees == context_b.callees
    assert context_a.call_chains == context_b.call_chains


def test_repository_pipeline_empty_result():
    class EmptyScorer:
        def score(self, issue: str):
            return {
                "files": [],
                "symbols": [],
                "routes": [],
            }

    graph_search = _build_graph_search()

    selector = EvidenceSelectorV2(
        graph_search=graph_search,
        relevance_scorer=EmptyScorer(),
    )

    builder = KnowledgeContextBuilder(
        graph_search=graph_search,
    )

    evidence = selector.select(
        "unknown issue",
    )

    context = builder.build(
        issue="unknown issue",
        evidence=evidence,
    )

    assert context.files == []
    assert context.symbols == []
    assert context.routes == []
    assert context.dependencies == []
    assert context.callers == []
    assert context.callees == []
    assert context.call_chains == []