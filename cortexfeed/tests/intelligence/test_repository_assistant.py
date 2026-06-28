# File: cortexfeed/tests/intelligence/test_repository_assistant.py

from cortexfeed.intelligence.repository_assistant import (
    RepositoryAssistant,
)
from cortexfeed.knowledge.context.models import (
    ContextDependency,
    ContextSymbol,
    RepositoryContext,
)


def _build_context() -> RepositoryContext:
    return RepositoryContext(
        issue="POST /login returns 500",
        files=[
            "auth/service.py",
        ],
        symbols=[
            ContextSymbol(
                name="login",
                node_type="FUNCTION",
            )
        ],
        routes=[
            "POST:/login",
        ],
        dependencies=[
            ContextDependency(
                source="login",
                target="validate_user",
                relationship="CALLS",
            )
        ],
        callers=[
            "controller",
        ],
        callees=[
            "validate_user",
        ],
        call_chains=[
            [
                "login",
                "validate_user",
                "create_token",
            ]
        ],
    )


def test_symbol_lookup_answer():
    assistant = RepositoryAssistant()

    context = _build_context()

    result = assistant.answer(
        query="Where is login handled?",
        context=context,
    )

    assert result.confidence > 0.0

    assert "login" in result.answer

    assert "function" in result.answer.lower()

    assert "login" in result.symbols


def test_route_lookup_answer():
    assistant = RepositoryAssistant()

    context = RepositoryContext(
        issue="route issue",
        routes=[
            "POST:/login",
        ],
    )

    result = assistant.answer(
        query="Trace POST /login",
        context=context,
    )

    assert result.confidence > 0.0

    assert "POST:/login" in result.answer

    assert result.routes == [
        "POST:/login",
    ]


def test_dependency_lookup_answer():
    assistant = RepositoryAssistant()

    context = RepositoryContext(
        issue="dependency issue",
        dependencies=[
            ContextDependency(
                source="PromiseService",
                target="PromiseRepository",
                relationship="DEPENDS_ON",
            )
        ],
    )

    result = assistant.answer(
        query="What depends on what?",
        context=context,
    )

    assert result.confidence > 0.0

    assert "PromiseService" in result.answer
    assert "PromiseRepository" in result.answer


def test_empty_context_returns_fallback():
    assistant = RepositoryAssistant()

    context = RepositoryContext(
        issue="unknown",
    )

    result = assistant.answer(
        query="Unknown query",
        context=context,
    )

    assert result.confidence == 0.0

    assert (
        result.answer
        == "No repository intelligence was found for the query."
    )

    assert result.symbols == []
    assert result.routes == []
    assert result.callers == []
    assert result.callees == []
    assert result.call_chains == []


def test_metadata_is_preserved():
    assistant = RepositoryAssistant()

    context = _build_context()

    result = assistant.answer(
        query="Where is login handled?",
        context=context,
    )

    assert result.symbols == [
        "login",
    ]

    assert result.routes == [
        "POST:/login",
    ]

    assert result.callers == [
        "controller",
    ]

    assert result.callees == [
        "validate_user",
    ]

    assert result.call_chains == [
        [
            "login",
            "validate_user",
            "create_token",
        ]
    ]


def test_deterministic_answers():
    assistant = RepositoryAssistant()

    context = _build_context()

    result_a = assistant.answer(
        query="Where is login handled?",
        context=context,
    )

    result_b = assistant.answer(
        query="Where is login handled?",
        context=context,
    )

    assert result_a.answer == result_b.answer
    assert result_a.confidence == result_b.confidence
    assert result_a.symbols == result_b.symbols
    assert result_a.routes == result_b.routes
    assert result_a.callers == result_b.callers
    assert result_a.callees == result_b.callees
    assert result_a.call_chains == result_b.call_chains


def test_symbol_lookup_has_higher_confidence_than_empty_context():
    assistant = RepositoryAssistant()

    populated = assistant.answer(
        query="Where is login handled?",
        context=_build_context(),
    )

    empty = assistant.answer(
        query="Where is login handled?",
        context=RepositoryContext(
            issue="unknown",
        ),
    )

    assert populated.confidence > empty.confidence


def test_route_answer_preserves_route_metadata():
    assistant = RepositoryAssistant()

    context = RepositoryContext(
        issue="route issue",
        routes=[
            "POST:/login",
        ],
        callers=[
            "controller",
        ],
        callees=[
            "validate_user",
        ],
    )

    result = assistant.answer(
        query="Route trace",
        context=context,
    )

    assert result.routes == [
        "POST:/login",
    ]

    assert result.callers == [
        "controller",
    ]

    assert result.callees == [
        "validate_user",
    ]