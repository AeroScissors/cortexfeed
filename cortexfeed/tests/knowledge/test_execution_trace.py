# File: cortexfeed/tests/knowledge/test_execution_trace.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.call_models import (
    CallTrace,
)


def test_multi_hop_trace():
    relationships = [
        CallRelationship(
            caller_symbol="Controller.login",
            callee_symbol="AuthService.login",
            caller_file="controller.py",
            callee_file="service.py",
            line_number=1,
        ),
        CallRelationship(
            caller_symbol="AuthService.login",
            callee_symbol="UserRepository.find_user",
            caller_file="service.py",
            callee_file="repository.py",
            line_number=2,
        ),
    ]

    adjacency = {}

    for relationship in relationships:
        adjacency.setdefault(
            relationship.caller_symbol,
            [],
        ).append(
            relationship.callee_symbol,
        )

    assert adjacency["Controller.login"] == [
        "AuthService.login",
    ]

    assert adjacency["AuthService.login"] == [
        "UserRepository.find_user",
    ]