# File: cortexfeed/tests/investigation/test_context_builder.py

from cortexfeed.investigation.context_builder import (
    ContextBuilder,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)


class FakeEvidenceSelector:
    def __init__(self, result):
        self.result = result

    def select(self, issue: str):
        return self.result


def _build_graph_search() -> GraphSearchV2:
    graph = Graph(
        nodes=[
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
                id="function:controller",
                type="FUNCTION",
                name="controller",
            ),
            GraphNode(
                id="route:POST:/login",
                type="ROUTE",
                name="POST:/login",
            ),
            GraphNode(
                id="symbol:DATABASE_URL",
                type="EXTERNAL_SYMBOL",
                name="DATABASE_URL",
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
            GraphEdge(
                source="route:POST:/login",
                target="function:login",
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


def test_build_populates_files():
    selector = FakeEvidenceSelector(
        {
            "files": [
                {
                    "path": "auth.py",
                    "score": 0.95,
                }
            ],
            "symbols": [],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "login issue",
    )

    assert len(context.files) == 1
    assert context.files[0].path == "auth.py"
    assert context.files[0].score == 0.95


def test_build_populates_symbols_and_routes():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": ["login"],
            "routes": ["POST:/login"],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "login issue",
    )

    assert "login" in context.symbols
    assert "POST:/login" in context.routes


def test_dependency_discovery():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": ["login"],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "login issue",
    )

    dependencies = {
        (
            dep.source,
            dep.target,
            dep.relationship,
        )
        for dep in context.dependencies
    }

    assert (
        "login",
        "validate_user",
        "DEPENDS_ON",
    ) in dependencies

    assert (
        "login",
        "DATABASE_URL",
        "DEPENDS_ON",
    ) in dependencies


def test_caller_discovery():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": ["login"],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "login issue",
    )

    assert any(
        dep.source == "controller"
        and dep.target == "login"
        and dep.relationship == "CALLS"
        for dep in context.dependencies
    )


def test_callee_discovery():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": ["login"],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "login issue",
    )

    assert any(
        dep.source == "login"
        and dep.target == "validate_user"
        and dep.relationship == "CALLS"
        for dep in context.dependencies
    )


def test_call_chain_generation():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": ["login"],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "login issue",
    )

    chains = [
        chain.chain
        for chain in context.call_chains
    ]

    assert any(
        chain[0] == "login"
        and "validate_user" in chain
        and "create_token" in chain
        for chain in chains
    )


def test_route_extraction_from_issue():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": [],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "POST /login returns 500",
    )

    assert any(
        route.startswith("POST")
        for route in context.routes
    )


def test_route_trace_creates_call_chain():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": [],
            "routes": ["POST:/login"],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "route issue",
    )

    route_chains = [
        chain.chain
        for chain in context.call_chains
        if chain.chain[0].startswith("Route(")
    ]

    assert len(route_chains) == 1

    chain = route_chains[0]

    assert "login" in chain
    assert "validate_user" in chain
    assert "create_token" in chain


def test_deduplicates_dependencies():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": [
                "login",
                "login",
            ],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "duplicate symbol issue",
    )

    unique = {
        (
            dep.source,
            dep.target,
            dep.relationship,
        )
        for dep in context.dependencies
    }

    assert len(unique) == len(
        context.dependencies
    )


def test_deduplicates_call_chains():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": [
                "login",
                "login",
            ],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "duplicate symbol issue",
    )

    serialized = [
        "->".join(chain.chain)
        for chain in context.call_chains
    ]

    assert len(serialized) == len(
        set(serialized)
    )


def test_empty_evidence_result():
    selector = FakeEvidenceSelector(
        {
            "files": [],
            "symbols": [],
            "routes": [],
        }
    )

    builder = ContextBuilder(
        graph_search=_build_graph_search(),
        evidence_selector=selector,
    )

    context = builder.build(
        "unknown issue",
    )

    assert context.issue == "unknown issue"
    assert context.files == []
    assert context.symbols == []
    assert context.routes == []
    assert context.dependencies == []
    assert context.call_chains == []