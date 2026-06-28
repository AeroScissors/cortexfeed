# File: cortexfeed/tests/knowledge/test_route_intelligence.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.route_intelligence import (
    RouteIntelligence,
)


def test_trace_route_to_target() -> None:
    route_map = {
        "POST /login": "AuthController.login",
    }

    relationships = [
        CallRelationship(
            caller_symbol="AuthController.login",
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

    intelligence = RouteIntelligence()

    trace = intelligence.trace_route(
        route_map=route_map,
        relationships=relationships,
        route="POST /login",
        target="UserRepository.find_user",
    )

    assert trace == [
        "POST /login",
        "AuthController.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]


def test_unknown_route_returns_empty_trace() -> None:
    intelligence = RouteIntelligence()

    trace = intelligence.trace_route(
        route_map={},
        relationships=[],
        route="POST /missing",
        target="Repository.find",
    )

    assert trace == []