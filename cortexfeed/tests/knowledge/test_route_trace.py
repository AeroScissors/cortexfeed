# File: cortexfeed/tests/knowledge/test_route_trace.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.route_trace import (
    RouteTraceBuilder,
)


def test_route_trace() -> None:
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

    builder = RouteTraceBuilder()

    trace = builder.trace(
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