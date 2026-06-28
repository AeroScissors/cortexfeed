# File: cortexfeed/tests/knowledge/v2/test_graph_search_v2.py

from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)


def _build_graph() -> Graph:
    nodes = [
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
        GraphNode(
            id="class:UserService",
            type="CLASS",
            name="UserService",
        ),
        GraphNode(
            id="class:AdminService",
            type="CLASS",
            name="AdminService",
        ),
        GraphNode(
            id="class:SuperAdminService",
            type="CLASS",
            name="SuperAdminService",
        ),
        GraphNode(
            id="symbol:DATABASE_URL",
            type="EXTERNAL_SYMBOL",
            name="DATABASE_URL",
        ),
    ]

    edges = [
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
        GraphEdge(
            source="class:AdminService",
            target="class:UserService",
            relationship="INHERITS",
        ),
        GraphEdge(
            source="class:SuperAdminService",
            target="class:AdminService",
            relationship="INHERITS",
        ),
    ]

    return Graph(
        nodes=nodes,
        edges=edges,
    )


def test_find_node():
    search = GraphSearchV2(
        _build_graph(),
    )

    node = search.find_node(
        "login",
    )

    assert node is not None
    assert node.id == "function:login"


def test_find_node_returns_none_for_missing_symbol():
    search = GraphSearchV2(
        _build_graph(),
    )

    result = search.find_node(
        "missing_symbol",
    )

    assert result is None


def test_get_dependencies():
    search = GraphSearchV2(
        _build_graph(),
    )

    deps = search.get_dependencies(
        "function:login",
    )

    names = {
        node.name
        for node in deps
    }

    assert "validate_user" in names
    assert "DATABASE_URL" in names


def test_get_dependents():
    search = GraphSearchV2(
        _build_graph(),
    )

    dependents = search.get_dependents(
        "function:validate_user",
    )

    names = {
        node.name
        for node in dependents
    }

    assert "login" in names


def test_find_callers():
    search = GraphSearchV2(
        _build_graph(),
    )

    callers = search.find_callers(
        "validate_user",
    )

    assert len(callers) == 1
    assert callers[0].name == "login"


def test_find_callees():
    search = GraphSearchV2(
        _build_graph(),
    )

    callees = search.find_callees(
        "login",
    )

    names = {
        node.name
        for node in callees
    }

    assert "validate_user" in names


def test_trace_call_chain():
    search = GraphSearchV2(
        _build_graph(),
    )

    chain = search.trace_call_chain(
        "login",
    )

    names = [
        node.name
        for node in chain
    ]

    assert "validate_user" in names
    assert "create_token" in names


def test_trace_call_chain_respects_depth():
    search = GraphSearchV2(
        _build_graph(),
    )

    chain = search.trace_call_chain(
        "login",
        max_depth=1,
    )

    names = {
        node.name
        for node in chain
    }

    assert "validate_user" in names
    assert "create_token" not in names


def test_trace_callers():
    search = GraphSearchV2(
        _build_graph(),
    )

    callers = search.trace_callers(
        "create_token",
    )

    names = {
        node.name
        for node in callers
    }

    assert "validate_user" in names
    assert "login" in names


def test_inheritance_tree_returns_parents_and_children():
    search = GraphSearchV2(
        _build_graph(),
    )

    tree = search.inheritance_tree(
        "AdminService",
    )

    names = {
        node.name
        for node in tree
    }

    assert "UserService" in names
    assert "SuperAdminService" in names


def test_route_trace():
    search = GraphSearchV2(
        _build_graph(),
    )

    result = search.route_trace(
        "POST",
        "/login",
    )

    names = {
        node.name
        for node in result
    }

    assert "login" in names
    assert "validate_user" in names
    assert "create_token" in names
    assert "DATABASE_URL" in names


def test_route_trace_returns_empty_for_unknown_route():
    search = GraphSearchV2(
        _build_graph(),
    )

    result = search.route_trace(
        "GET",
        "/missing",
    )

    assert result == []


def test_impact_analysis():
    search = GraphSearchV2(
        _build_graph(),
    )

    impact = search.impact_analysis(
        "validate_user",
    )

    assert impact["callers"] == ["login"]
    assert impact["callees"] == ["create_token"]

    assert "login" in impact["dependents"]
    assert "create_token" in impact["dependencies"]


def test_impact_analysis_for_missing_symbol():
    search = GraphSearchV2(
        _build_graph(),
    )

    impact = search.impact_analysis(
        "missing",
    )

    assert impact == {
        "callers": [],
        "callees": [],
        "dependencies": [],
        "dependents": [],
    }


def test_repository_context():
    search = GraphSearchV2(
        _build_graph(),
    )

    context = search.repository_context(
        "AdminService",
    )

    assert context["node"]["name"] == "AdminService"

    inheritance = set(
        context["inheritance"]
    )

    assert "UserService" in inheritance
    assert "SuperAdminService" in inheritance


def test_repository_context_for_missing_symbol():
    search = GraphSearchV2(
        _build_graph(),
    )

    context = search.repository_context(
        "missing",
    )

    assert context == {}