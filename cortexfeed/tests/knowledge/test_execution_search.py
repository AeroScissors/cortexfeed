# File: cortexfeed/tests/knowledge/test_execution_search.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.execution_search import (
    ExecutionSearch,
)


def _relationships() -> list[CallRelationship]:
    return [
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


def test_find_callers() -> None:
    search = ExecutionSearch()

    callers = search.find_callers(
        _relationships(),
        "AuthService.login",
    )

    assert callers == [
        "Controller.login",
    ]


def test_find_callees() -> None:
    search = ExecutionSearch()

    callees = search.find_callees(
        _relationships(),
        "Controller.login",
    )

    assert callees == [
        "AuthService.login",
    ]


def test_trace() -> None:
    search = ExecutionSearch()

    path = search.trace(
        relationships=_relationships(),
        start="Controller.login",
        target="UserRepository.find_user",
    )

    assert path == [
        "Controller.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]


def test_has_path() -> None:
    search = ExecutionSearch()

    assert search.has_path(
        relationships=_relationships(),
        start="Controller.login",
        target="UserRepository.find_user",
    )


def test_has_no_path() -> None:
    search = ExecutionSearch()

    assert not search.has_path(
        relationships=_relationships(),
        start="Unknown.start",
        target="UserRepository.find_user",
    )