# File: cortexfeed/tests/knowledge/test_query_parser.py

from cortexfeed.knowledge.graph.v3.query_parser import (
    QueryParser,
)


def test_parse_who_calls() -> None:
    parser = QueryParser()

    intent = parser.parse(
        "Who calls AuthService.login?"
    )

    assert intent.intent_type == "who_calls"
    assert intent.symbol == "AuthService.login"


def test_parse_what_does_call() -> None:
    parser = QueryParser()

    intent = parser.parse(
        "What does AuthController.login call?"
    )

    assert intent.intent_type == "what_does_call"
    assert intent.symbol == "AuthController.login"


def test_parse_can_reach() -> None:
    parser = QueryParser()

    intent = parser.parse(
        "Can AuthController.login reach UserRepository.find_user?"
    )

    assert intent.intent_type == "can_reach"
    assert (
        intent.start
        == "AuthController.login"
    )

    assert (
        intent.target
        == "UserRepository.find_user"
    )


def test_parse_trace() -> None:
    parser = QueryParser()

    intent = parser.parse(
        "Trace AuthController.login -> UserRepository.find_user"
    )

    assert intent.intent_type == "trace"

    assert (
        intent.start
        == "AuthController.login"
    )

    assert (
        intent.target
        == "UserRepository.find_user"
    )


def test_parse_unknown() -> None:
    parser = QueryParser()

    intent = parser.parse(
        "Why is QueryRouter unreachable?"
    )

    assert intent.intent_type == "unknown"