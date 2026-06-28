# File: cortexfeed/tests/investigation/test_pipeline_trace.py

from __future__ import annotations

from pathlib import Path

from cortexfeed.investigation.orchestrator.engine import (
    InvestigationEngine,
)


def test_pipeline_trace(tmp_path: Path) -> None:
    """
    Diagnostic integration test.

    Purpose:
        Trace the complete Investigation V2 pipeline and
        immediately reveal where execution stops producing data.

    This test is intentionally observational rather than strict.
    It validates that every stage executes and emits useful
    debugging information.

    Flow:

        Request
            ↓
        Intent
            ↓
        Plan
            ↓
        Evidence
            ↓
        Facts
            ↓
        Hypotheses
            ↓
        Prompt
            ↓
        Persistence
    """

    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)

    project_root = tmp_path / "project"
    project_root.mkdir(parents=True, exist_ok=True)

    sample_file = project_root / "app.py"
    sample_file.write_text(
        """
def get_promise():
    raise RuntimeError("Connection refused")
""".strip(),
        encoding="utf-8",
    )

    engine = InvestigationEngine(
        sessions_root=sessions_root,
        project_root=project_root,
    )

    result = engine.investigate(
        "GET /promise returns 404 and connection refused errors",
        project_name="pipeline-trace",
    )

    session = result.session

    print("\n========== INVESTIGATION TRACE ==========")

    print(
        f"Intent Type: "
        f"{result.intent.investigation_type.value}"
    )

    print(
        f"Domain: "
        f"{result.intent.domain.value}"
    )

    print(
        f"Confidence: "
        f"{result.intent.confidence}"
    )

    print("\n--- Planned Evidence ---")

    for requirement in result.plan.collection_order:
        print(
            f"- {requirement.evidence_type.value}"
        )

    evidence_items = session.evidence.list()

    print("\n--- Collected Evidence ---")
    print(f"Count: {len(evidence_items)}")

    for evidence in evidence_items:
        print(
            f"- {evidence.evidence_type}"
        )

        print(
            f"  path={evidence.path}"
        )

        if evidence.file_hash:
            print(
                f"  hash={evidence.file_hash[:12]}"
            )

        if evidence.metadata:
            print(
                f"  metadata={evidence.metadata}"
            )

    print("\n--- FACT REGISTRY ---")
    print(type(session.facts))
    print(dir(session.facts))

    facts = session.facts.list_facts()

    print("\n--- Facts ---")
    print(f"Count: {len(facts)}")

    for fact in facts:
        print(f"- {fact}")

    print("\n--- HYPOTHESIS REGISTRY COUNT ---")
    print(session.hypotheses.list())

    for hypothesis in session.hypotheses.list():
        print(hypothesis)

    prompt_package = result.prompt_package

    print("\n--- Prompt ---")

    if hasattr(prompt_package, "prompt"):
        prompt_text = prompt_package.prompt
    elif hasattr(prompt_package, "content"):
        prompt_text = prompt_package.content
    else:
        prompt_text = str(prompt_package)

    print(prompt_text[:1000])

    print("\n--- Session Metadata ---")
    print(
        f"Evidence Count: "
        f"{result.evidence_count}"
    )
    print(
        f"Fact Count: "
        f"{result.fact_count}"
    )
    print(
        f"Hypothesis Count: "
        f"{result.hypothesis_count}"
    )

    print("========================================\n")

    assert result.intent is not None
    assert result.plan is not None
    assert result.prompt_package is not None

    assert result.project_name == "pipeline-trace"

    assert sessions_root.exists()

    # Diagnostic assertions:
    # these should never fail unless a stage completely breaks.
    assert result.evidence_count >= 0
    assert result.fact_count >= 0
    assert result.hypothesis_count >= 0