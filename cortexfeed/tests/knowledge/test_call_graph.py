# File: cortexfeed/tests/knowledge/test_call_graph.py

from cortexfeed.knowledge.graph.v3.call_graph import (
    CallGraphBuilder,
)
from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.models import (
    EdgeType,
)


def test_build_call_graph_edges() -> None:
    relationships = [
        CallRelationship(
            caller_symbol="Controller.login",
            callee_symbol="AuthService.login",
            caller_file="controller.py",
            callee_file="service.py",
            line_number=10,
        ),
        CallRelationship(
            caller_symbol="AuthService.login",
            callee_symbol="UserRepository.find_user",
            caller_file="service.py",
            callee_file="repository.py",
            line_number=15,
        ),
    ]

    builder = CallGraphBuilder()

    edges = builder.build(relationships)

    assert len(edges) == 2

    assert edges[0].source == "Controller.login"
    assert edges[0].target == "AuthService.login"
    assert edges[0].edge_type == EdgeType.CALLS

    assert edges[1].source == "AuthService.login"
    assert edges[1].target == "UserRepository.find_user"
    assert edges[1].edge_type == EdgeType.CALLS