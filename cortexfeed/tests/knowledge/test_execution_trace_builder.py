# File: cortexfeed/tests/knowledge/test_execution_trace_builder.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.execution_trace import (
    ExecutionTraceBuilder,
)


def test_build_execution_trace() -> None:
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

    builder = ExecutionTraceBuilder()

    trace = builder.trace(
        relationships=relationships,
        start="Controller.login",
        target="UserRepository.find_user",
    )

    assert trace == [
        "Controller.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]