from cortexfeed.intelligence.capabilities.call_chain import (
    CallChainCapability,
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


def test_chain_found():
    capability = CallChainCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert result.confidence > 0.0
    assert result.execution_path[0] == "login"


def test_chain_contains_all_nodes():
    capability = CallChainCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert "login" in result.execution_path
    assert "validate_user" in result.execution_path
    assert "create_token" in result.execution_path


def test_symbol_missing():
    capability = CallChainCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "missing_symbol",
    )

    assert result.confidence == 0.0


def test_metadata_present():
    capability = CallChainCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
    )

    assert result.metadata["root_symbol"] == "login"
    assert result.metadata["chain_length"] > 0


def test_depth_limit():
    capability = CallChainCapability(
        _build_graph_search(),
    )

    result = capability.execute(
        "login",
        max_depth=1,
    )

    assert len(result.execution_path) == 2


def test_deterministic():
    capability = CallChainCapability(
        _build_graph_search(),
    )

    result_a = capability.execute(
        "login",
    )

    result_b = capability.execute(
        "login",
    )

    assert result_a == result_b