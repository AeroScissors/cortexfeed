# File: cortexfeed/tests/knowledge/test_repository_query_service.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.repository_query_service import (
    RepositoryQueryService,
)


def _relationships():
    return [
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


def test_who_calls_query():
    service = RepositoryQueryService()

    result = service.who_calls(
        relationships=_relationships(),
        symbol="AuthService.login",
    )

    assert result == [
        "AuthController.login",
    ]


def test_trace_query():
    service = RepositoryQueryService()

    result = service.trace(
        relationships=_relationships(),
        start="AuthController.login",
        target="UserRepository.find_user",
    )

    assert result == [
        "AuthController.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]