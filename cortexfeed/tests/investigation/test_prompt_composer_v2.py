# File: cortexfeed/tests/investigation/test_prompt_composer_v2.py

from cortexfeed.investigation.models import (
    ContextCallChain,
    ContextDependency,
    ContextFile,
    InvestigationContext,
)
from cortexfeed.investigation.prompts.composer_v2 import (
    PromptComposerV2,
)


class Fact:
    def __init__(self, content: str) -> None:
        self.content = content


class Hypothesis:
    def __init__(self, content: str) -> None:
        self.content = content


def _build_context() -> InvestigationContext:
    return InvestigationContext(
        issue="POST /login returns 500",
        files=[
            ContextFile(
                path="auth/service.py",
                score=0.95,
            ),
            ContextFile(
                path="auth/repository.py",
                score=0.90,
            ),
        ],
        dependencies=[
            ContextDependency(
                source="login",
                target="validate_user",
                relationship="CALLS",
            ),
            ContextDependency(
                source="validate_user",
                target="create_token",
                relationship="CALLS",
            ),
        ],
        call_chains=[
            ContextCallChain(
                chain=[
                    "login",
                    "validate_user",
                    "create_token",
                ]
            )
        ],
        routes=[
            "POST:/login",
        ],
        symbols=[
            "login",
            "validate_user",
        ],
    )


def test_compose_generates_complete_prompt():
    composer = PromptComposerV2()

    context = _build_context()

    prompt = composer.compose(
        issue="POST /login returns 500",
        context=context,
        facts=[
            Fact(
                "Endpoint returns HTTP 500",
            )
        ],
        hypotheses=[
            Hypothesis(
                "Token generation fails",
            )
        ],
    )

    assert "INVESTIGATION ISSUE" in prompt
    assert "POST /login returns 500" in prompt

    assert "RELEVANT FILES" in prompt
    assert "auth/service.py" in prompt

    assert "RELEVANT SYMBOLS" in prompt
    assert "login" in prompt

    assert "DEPENDENCIES" in prompt
    assert "validate_user" in prompt

    assert "EXECUTION PATHS" in prompt
    assert "create_token" in prompt

    assert "ROUTE CONTEXT" in prompt
    assert "POST:/login" in prompt

    assert "FACTS" in prompt
    assert "Endpoint returns HTTP 500" in prompt

    assert "HYPOTHESES" in prompt
    assert "Token generation fails" in prompt

    assert "INVESTIGATION INSTRUCTIONS" in prompt


def test_compose_with_empty_context():
    composer = PromptComposerV2()

    context = InvestigationContext(
        issue="Unknown issue",
    )

    prompt = composer.compose(
        issue="Unknown issue",
        context=context,
        facts=[],
        hypotheses=[],
    )

    assert "INVESTIGATION ISSUE" in prompt
    assert "Unknown issue" in prompt

    assert "RELEVANT FILES" not in prompt
    assert "RELEVANT SYMBOLS" not in prompt
    assert "DEPENDENCIES" not in prompt
    assert "EXECUTION PATHS" not in prompt
    assert "ROUTE CONTEXT" not in prompt
    assert "FACTS" not in prompt
    assert "HYPOTHESES" not in prompt

    assert "INVESTIGATION INSTRUCTIONS" in prompt


def test_file_limit_is_enforced():
    composer = PromptComposerV2()

    context = InvestigationContext(
        issue="test",
        files=[
            ContextFile(
                path=f"file_{i}.py",
                score=1.0,
            )
            for i in range(50)
        ],
    )

    section = composer._format_files(
        context,
    )

    assert "file_0.py" in section
    assert "file_19.py" in section
    assert "file_20.py" not in section


def test_symbol_limit_is_enforced():
    composer = PromptComposerV2()

    context = InvestigationContext(
        issue="test",
        symbols=[
            f"symbol_{i}"
            for i in range(50)
        ],
    )

    section = composer._format_symbols(
        context,
    )

    assert "symbol_0" in section
    assert "symbol_29" in section
    assert "symbol_30" not in section


def test_dependency_limit_is_enforced():
    composer = PromptComposerV2()

    context = InvestigationContext(
        issue="test",
        dependencies=[
            ContextDependency(
                source=f"source_{i}",
                target=f"target_{i}",
                relationship="CALLS",
            )
            for i in range(100)
        ],
    )

    section = composer._format_dependencies(
        context,
    )

    assert "source_0" in section
    assert "source_49" in section
    assert "source_50" not in section


def test_call_chain_limit_is_enforced():
    composer = PromptComposerV2()

    context = InvestigationContext(
        issue="test",
        call_chains=[
            ContextCallChain(
                chain=[
                    f"node_{i}",
                ]
            )
            for i in range(50)
        ],
    )

    section = composer._format_call_chains(
        context,
    )

    assert "node_0" in section
    assert "node_19" in section
    assert "node_20" not in section


def test_formats_dependency_graph():
    composer = PromptComposerV2()

    context = InvestigationContext(
        issue="test",
        dependencies=[
            ContextDependency(
                source="controller",
                target="service",
                relationship="CALLS",
            ),
        ],
    )

    section = composer._format_dependencies(
        context,
    )

    assert "controller" in section
    assert "service" in section
    assert "->" in section


def test_formats_call_chain():
    composer = PromptComposerV2()

    context = InvestigationContext(
        issue="test",
        call_chains=[
            ContextCallChain(
                chain=[
                    "controller",
                    "service",
                    "repository",
                ]
            )
        ],
    )

    section = composer._format_call_chains(
        context,
    )

    assert "controller" in section
    assert "service" in section
    assert "repository" in section


def test_formats_facts():
    composer = PromptComposerV2()

    section = composer._format_facts(
        [
            Fact(
                "Database connection failed",
            ),
            Fact(
                "Request reached controller",
            ),
        ]
    )

    assert "FACTS" in section
    assert "Database connection failed" in section
    assert "Request reached controller" in section


def test_formats_hypotheses():
    composer = PromptComposerV2()

    section = composer._format_hypotheses(
        [
            Hypothesis(
                "Database unavailable",
            ),
            Hypothesis(
                "Token generation bug",
            ),
        ]
    )

    assert "HYPOTHESES" in section
    assert "1. Database unavailable" in section
    assert "2. Token generation bug" in section


def test_prompt_contains_investigation_instructions():
    composer = PromptComposerV2()

    prompt = composer.compose(
        issue="login failure",
        context=InvestigationContext(
            issue="login failure",
        ),
        facts=[],
        hypotheses=[],
    )

    assert (
        "Use the supplied repository intelligence."
        in prompt
    )

    assert (
        "Do not speculate beyond the provided context."
        in prompt
    )


def test_prompt_length_for_real_context():
    composer = PromptComposerV2()

    prompt = composer.compose(
        issue="POST /login returns 500",
        context=_build_context(),
        facts=[
            Fact(
                "Request reaches service layer",
            )
        ],
        hypotheses=[
            Hypothesis(
                "Repository throws exception",
            )
        ],
    )

    assert len(prompt) > 300