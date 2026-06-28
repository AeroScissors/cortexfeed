# File: cortexfeed/tests/knowledge/test_repository_question_engine.py

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.repository_question_engine import (
    RepositoryQuestionEngine,
)


def _relationships() -> list[CallRelationship]:
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


def test_who_calls() -> None:
    engine = RepositoryQuestionEngine()

    callers = engine.who_calls(
        relationships=_relationships(),
        symbol="AuthService.login",
    )

    assert callers == [
        "AuthController.login",
    ]


def test_what_does_call() -> None:
    engine = RepositoryQuestionEngine()

    callees = engine.what_does_call(
        relationships=_relationships(),
        symbol="AuthController.login",
    )

    assert callees == [
        "AuthService.login",
    ]


def test_can_reach() -> None:
    engine = RepositoryQuestionEngine()

    assert engine.can_reach(
        relationships=_relationships(),
        start="AuthController.login",
        target="UserRepository.find_user",
    )


def test_trace() -> None:
    engine = RepositoryQuestionEngine()

    trace = engine.trace(
        relationships=_relationships(),
        start="AuthController.login",
        target="UserRepository.find_user",
    )

    assert trace == [
        "AuthController.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]


def test_trace_route() -> None:
    route_map = {
        "POST /login": "AuthController.login",
    }

    engine = RepositoryQuestionEngine()

    trace = engine.trace_route(
        route_map=route_map,
        relationships=_relationships(),
        route="POST /login",
        target="UserRepository.find_user",
    )

    assert trace == [
        "POST /login",
        "AuthController.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]