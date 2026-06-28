# File: cortexfeed/tests/knowledge/v2/test_graph_builder_v2.py

from cortexfeed.knowledge.graph.v2.graph_builder_v2 import (
    build_graph_v2,
    NODE_CLASS,
    NODE_DECORATOR,
    NODE_EXTERNAL_SYMBOL,
    NODE_FILE,
    NODE_FUNCTION,
    NODE_METHOD,
    NODE_MODULE,
    NODE_ROUTE,
    EDGE_CALLS,
    EDGE_DECORATED_BY,
    EDGE_DEFINES,
    EDGE_EXPOSES_ROUTE,
    EDGE_IMPORTS,
    EDGE_INHERITS,
    EDGE_INSTANTIATES,
    EDGE_REFERENCES,
)


def _node(graph, node_id: str):
    return next(
        node
        for node in graph.nodes
        if node.id == node_id
    )


def _edge_exists(
    graph,
    source: str,
    target: str,
    relationship: str,
) -> bool:
    return any(
        edge.source == source
        and edge.target == target
        and edge.relationship == relationship
        for edge in graph.edges
    )


def test_creates_file_class_function_method_and_route_nodes():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "classes": [
                    {"name": "UserService"},
                ],
                "functions": [
                    {"name": "helper"},
                ],
                "methods": [
                    {
                        "class_name": "UserService",
                        "name": "create_user",
                    },
                ],
                "routes": [
                    {
                        "method": "GET",
                        "path": "/users",
                    },
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _node(graph, "file:service.py").type == NODE_FILE
    assert _node(graph, "class:UserService").type == NODE_CLASS
    assert _node(graph, "function:helper").type == NODE_FUNCTION
    assert (
        _node(
            graph,
            "method:UserService.create_user",
        ).type
        == NODE_METHOD
    )
    assert (
        _node(
            graph,
            "route:GET:/users",
        ).type
        == NODE_ROUTE
    )


def test_creates_defines_edges():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "classes": [
                    {"name": "UserService"},
                ],
                "functions": [
                    {"name": "helper"},
                ],
                "methods": [
                    {
                        "class_name": "UserService",
                        "name": "create_user",
                    },
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _edge_exists(
        graph,
        "file:service.py",
        "class:UserService",
        EDGE_DEFINES,
    )

    assert _edge_exists(
        graph,
        "file:service.py",
        "function:helper",
        EDGE_DEFINES,
    )

    assert _edge_exists(
        graph,
        "file:service.py",
        "method:UserService.create_user",
        EDGE_DEFINES,
    )


def test_creates_import_edges_and_module_nodes():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "imports": [
                    {
                        "module": "pathlib",
                    },
                    {
                        "module": "os",
                    },
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _node(
        graph,
        "module:pathlib",
    ).type == NODE_MODULE

    assert _node(
        graph,
        "module:os",
    ).type == NODE_MODULE

    assert _edge_exists(
        graph,
        "file:service.py",
        "module:pathlib",
        EDGE_IMPORTS,
    )

    assert _edge_exists(
        graph,
        "file:service.py",
        "module:os",
        EDGE_IMPORTS,
    )


def test_creates_route_edges():
    symbol_index = {
        "files": [
            {
                "file_path": "routes.py",
                "routes": [
                    {
                        "method": "POST",
                        "path": "/login",
                    }
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _edge_exists(
        graph,
        "file:routes.py",
        "route:POST:/login",
        EDGE_EXPOSES_ROUTE,
    )


def test_creates_call_edges_between_functions():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "functions": [
                    {"name": "controller"},
                    {"name": "create_user"},
                ],
                "calls": [
                    {
                        "caller": "controller",
                        "target": "create_user",
                    }
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _edge_exists(
        graph,
        "function:controller",
        "function:create_user",
        EDGE_CALLS,
    )


def test_creates_external_symbol_when_call_target_missing():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "calls": [
                    {
                        "caller": "controller",
                        "target": "external_api",
                    }
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    node = _node(
        graph,
        "symbol:external_api",
    )

    assert node.type == NODE_EXTERNAL_SYMBOL

    assert _edge_exists(
        graph,
        "function:controller",
        "symbol:external_api",
        EDGE_CALLS,
    )


def test_creates_reference_edges():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "references": [
                    {
                        "symbol": "DATABASE_URL",
                    }
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _node(
        graph,
        "symbol:DATABASE_URL",
    ).type == NODE_EXTERNAL_SYMBOL

    assert _edge_exists(
        graph,
        "file:service.py",
        "symbol:DATABASE_URL",
        EDGE_REFERENCES,
    )


def test_creates_instantiation_edges():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "instantiations": [
                    {
                        "class_name": "UserRepository",
                    }
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _edge_exists(
        graph,
        "file:service.py",
        "class:UserRepository",
        EDGE_INSTANTIATES,
    )


def test_creates_inheritance_edges():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "inherits": [
                    {
                        "class_name": "AdminService",
                        "parent": "UserService",
                    }
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _edge_exists(
        graph,
        "class:AdminService",
        "class:UserService",
        EDGE_INHERITS,
    )


def test_creates_decorator_edges_for_functions_and_methods():
    symbol_index = {
        "files": [
            {
                "file_path": "routes.py",
                "functions": [
                    {
                        "name": "get_users",
                        "decorators": [
                            "router.get",
                        ],
                    }
                ],
                "methods": [
                    {
                        "class_name": "UserService",
                        "name": "create_user",
                        "decorators": [
                            "transactional",
                        ],
                    }
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    assert _node(
        graph,
        "decorator:router.get",
    ).type == NODE_DECORATOR

    assert _node(
        graph,
        "decorator:transactional",
    ).type == NODE_DECORATOR

    assert _edge_exists(
        graph,
        "function:get_users",
        "decorator:router.get",
        EDGE_DECORATED_BY,
    )

    assert _edge_exists(
        graph,
        "method:UserService.create_user",
        "decorator:transactional",
        EDGE_DECORATED_BY,
    )


def test_deduplicates_duplicate_edges():
    symbol_index = {
        "files": [
            {
                "file_path": "service.py",
                "imports": [
                    {"module": "os"},
                    {"module": "os"},
                ],
            }
        ]
    }

    graph = build_graph_v2(symbol_index)

    matching_edges = [
        edge
        for edge in graph.edges
        if edge.source == "file:service.py"
        and edge.target == "module:os"
        and edge.relationship == EDGE_IMPORTS
    ]

    assert len(matching_edges) == 1