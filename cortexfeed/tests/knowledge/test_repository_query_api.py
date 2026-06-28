# File: cortexfeed/tests/knowledge/test_repository_query_api.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.repository_query_api import (
    RepositoryQueryAPI,
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


def test_query_who_calls():
    api = RepositoryQueryAPI()

    result = api.query(
        "Who calls AuthService.login?",
        _relationships(),
    )

    assert result == [
        "AuthController.login",
    ]


def test_query_trace():
    api = RepositoryQueryAPI()

    result = api.query(
        "Trace AuthController.login -> UserRepository.find_user",
        _relationships(),
    )

    assert result == [
        "AuthController.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]