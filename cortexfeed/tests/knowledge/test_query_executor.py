# File: cortexfeed/tests/knowledge/test_query_executor.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.query_executor import (
    QueryExecutor,
)
from cortexfeed.knowledge.graph.v3.query_models import (
    QueryIntent,
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


def test_execute_who_calls():
    executor = QueryExecutor()

    result = executor.execute(
        QueryIntent(
            intent_type="who_calls",
            symbol="AuthService.login",
        ),
        _relationships(),
    )

    assert result == [
        "AuthController.login",
    ]


def test_execute_trace():
    executor = QueryExecutor()

    result = executor.execute(
        QueryIntent(
            intent_type="trace",
            start="AuthController.login",
            target="UserRepository.find_user",
        ),
        _relationships(),
    )

    assert result == [
        "AuthController.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]