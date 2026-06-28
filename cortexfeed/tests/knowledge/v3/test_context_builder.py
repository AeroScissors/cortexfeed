# File: cortexfeed/tests/knowledge/v3/test_context_builder.py

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
from cortexfeed.knowledge.ranking.v2.models import (
    EvidencePackage,
    RankedEvidence,
)


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


def test_build_creates_repository_context():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="login",
                score=1.0,
                source="symbol",
            )
        ]
    )

    context = builder.build(
        issue="login failure",
        evidence=evidence,
    )

    assert context.issue == "login failure"


def test_seed_files_are_preserved():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        files=[
            RankedEvidence(
                symbol="auth/service.py",
                score=1.0,
                source="file",
            )
        ]
    )

    context = builder.build(
        issue="login failure",
        evidence=evidence,
    )

    assert "auth/service.py" in context.files


def test_seed_routes_are_preserved():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        routes=[
            RankedEvidence(
                symbol="POST:/login",
                score=1.0,
                source="route",
            )
        ]
    )

    context = builder.build(
        issue="route failure",
        evidence=evidence,
    )

    assert "POST:/login" in context.routes


def test_symbol_expansion():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="login",
                score=1.0,
                source="symbol",
            )
        ]
    )

    context = builder.build(
        issue="login failure",
        evidence=evidence,
    )

    names = {
        symbol.name
        for symbol in context.symbols
    }

    assert "login" in names


def test_dependency_expansion():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="login",
                score=1.0,
                source="symbol",
            )
        ]
    )

    context = builder.build(
        issue="login failure",
        evidence=evidence,
    )

    dependencies = {
        (
            dep.source,
            dep.target,
        )
        for dep in context.dependencies
    }

    assert (
        "login",
        "validate_user",
    ) in dependencies

    assert (
        "login",
        "DATABASE_URL",
    ) in dependencies


def test_caller_expansion():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="login",
                score=1.0,
                source="symbol",
            )
        ]
    )

    context = builder.build(
        issue="login failure",
        evidence=evidence,
    )

    assert "controller" in context.callers


def test_callee_expansion():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="login",
                score=1.0,
                source="symbol",
            )
        ]
    )

    context = builder.build(
        issue="login failure",
        evidence=evidence,
    )

    assert "validate_user" in context.callees


def test_call_chain_generation():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="login",
                score=1.0,
                source="symbol",
            )
        ]
    )

    context = builder.build(
        issue="login failure",
        evidence=evidence,
    )

    assert len(context.call_chains) == 1

    chain = context.call_chains[0]

    assert chain[0] == "login"
    assert "validate_user" in chain
    assert "create_token" in chain


def test_route_expansion_creates_execution_chain():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        routes=[
            RankedEvidence(
                symbol="POST:/login",
                score=1.0,
                source="route",
            )
        ]
    )

    context = builder.build(
        issue="route failure",
        evidence=evidence,
    )

    assert len(context.call_chains) == 1

    route_chain = context.call_chains[0]

    assert route_chain[0] == "Route(POST:/login)"
    assert "login" in route_chain
    assert "validate_user" in route_chain


def test_deduplicates_files():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        files=[
            RankedEvidence(
                symbol="auth.py",
                score=1.0,
                source="file",
            ),
            RankedEvidence(
                symbol="auth.py",
                score=0.5,
                source="file",
            ),
        ]
    )

    context = builder.build(
        issue="duplicate file",
        evidence=evidence,
    )

    assert context.files == ["auth.py"]


def test_deduplicates_symbols():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="login",
                score=1.0,
                source="symbol",
            ),
            RankedEvidence(
                symbol="login",
                score=0.5,
                source="symbol",
            ),
        ]
    )

    context = builder.build(
        issue="duplicate symbol",
        evidence=evidence,
    )

    assert len(context.symbols) == 1


def test_unknown_symbol_is_ignored():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    evidence = EvidencePackage(
        symbols=[
            RankedEvidence(
                symbol="missing_symbol",
                score=1.0,
                source="symbol",
            )
        ]
    )

    context = builder.build(
        issue="unknown symbol",
        evidence=evidence,
    )

    assert context.symbols == []
    assert context.dependencies == []
    assert context.callers == []
    assert context.callees == []


def test_empty_evidence_package():
    builder = KnowledgeContextBuilder(
        graph_search=_build_graph_search(),
    )

    context = builder.build(
        issue="empty issue",
        evidence=EvidencePackage(),
    )

    assert context.issue == "empty issue"
    assert context.files == []
    assert context.symbols == []
    assert context.routes == []
    assert context.dependencies == []
    assert context.callers == []
    assert context.callees == []
    assert context.call_chains == []