# File: cortexfeed/tests/investigation/test_investigation_smoke.py

from __future__ import annotations

from datetime import datetime, timezone

from cortexfeed.investigation.analyst.fact_extractor import (
    Evidence,
    FactExtractor,
)
from cortexfeed.investigation.analyst.hypothesis_engine import (
    HypothesisEngine,
)
from cortexfeed.investigation.planner.intent_analyzer import (
    RuleBasedIntentClassifier,
)
from cortexfeed.investigation.prompts.composer import (
    PromptComposer,
)


class TestSmokeIntentClassification:
    def test_real_intent_classifier_backend_debugging(
        self,
    ) -> None:
        classifier = RuleBasedIntentClassifier()

        intent = classifier.classify(
            "Fix backend sync issue causing API failures",
        )

        assert (
            intent.investigation_type.value
            == "debugging"
        )

        assert (
            intent.domain.value
            == "backend"
        )

        assert intent.confidence > 0.0

    def test_real_intent_classifier_auth_security(
        self,
    ) -> None:
        classifier = RuleBasedIntentClassifier()

        intent = classifier.classify(
            "JWT token authentication failure",
        )

        assert (
            intent.investigation_type.value
            == "security"
        )

        assert (
            intent.domain.value
            == "auth"
        )

        assert intent.confidence > 0.0


class TestSmokeAnalysisPipeline:
    def test_real_fact_to_hypothesis_flow_404(
        self,
    ) -> None:
        evidence = Evidence(
            id="ev-404",
            source="test",
            content="GET /promise returns 404",
            created_at=datetime.now(
                timezone.utc,
            ),
        )

        extractor = FactExtractor()

        facts = extractor.extract(
            [evidence],
        )

        assert len(facts) == 1

        fact = facts[0]

        assert (
            fact.statement
            == "GET /promise returns 404"
        )

        engine = HypothesisEngine()

        hypotheses = engine.generate(
            facts,
        )

        hypotheses = engine.update_status(
            hypotheses,
        )

        statements = {
            hypothesis.statement
            for hypothesis in hypotheses
        }

        assert (
            "Requested route is not registered"
            in statements
        )

        assert (
            "Request path is incorrect"
            in statements
        )

    def test_real_fact_to_hypothesis_flow_connection_refused(
        self,
    ) -> None:
        evidence = Evidence(
            id="ev-connection",
            source="test",
            content="Connection refused while calling backend service",
            created_at=datetime.now(
                timezone.utc,
            ),
        )

        extractor = FactExtractor()

        facts = extractor.extract(
            [evidence],
        )

        engine = HypothesisEngine()

        hypotheses = engine.generate(
            facts,
        )

        statements = {
            hypothesis.statement
            for hypothesis in hypotheses
        }

        assert (
            "Target service is not running"
            in statements
        )

        assert (
            "Network configuration issue exists"
            in statements
        )

    def test_real_fact_to_hypothesis_flow_timeout(
        self,
    ) -> None:
        evidence = Evidence(
            id="ev-timeout",
            source="test",
            content="Database request timeout after 30 seconds",
            created_at=datetime.now(
                timezone.utc,
            ),
        )

        extractor = FactExtractor()

        facts = extractor.extract(
            [evidence],
        )

        engine = HypothesisEngine()

        hypotheses = engine.generate(
            facts,
        )

        statements = {
            hypothesis.statement
            for hypothesis in hypotheses
        }

        assert (
            "Dependency is responding too slowly"
            in statements
        )


class TestSmokePromptComposition:
    def test_real_prompt_composition(
        self,
    ) -> None:
        composer = PromptComposer()

        package = composer.compose(
            project="cortexfeed",
            current_issue="GET /promise returns 404",
            facts=[
                "GET /promise returns 404",
            ],
            evidence=[
                "server.log",
            ],
            hypotheses=[
                "Requested route is not registered",
            ],
            timeline=[
                "Investigation started",
            ],
            task="Determine root cause",
        )

        assert (
            package.template_name
            == "debugging"
        )

        assert (
            package.sections["project"]
            == "cortexfeed"
        )

        assert (
            package.sections["current_issue"]
            == "GET /promise returns 404"
        )

        assert (
            package.sections["verified_facts"]
            == [
                "GET /promise returns 404",
            ]
        )

        assert (
            package.sections["active_hypotheses"]
            == [
                "Requested route is not registered",
            ]
        )

        assert (
            package.sections["task"]
            == "Determine root cause"
        )

    def test_real_prompt_composition_is_deterministic(
        self,
    ) -> None:
        composer = PromptComposer()

        first = composer.compose(
            project="demo",
            current_issue="404",
            facts=["404"],
            hypotheses=["missing route"],
            task="debug",
        )

        second = composer.compose(
            project="demo",
            current_issue="404",
            facts=["404"],
            hypotheses=["missing route"],
            task="debug",
        )

        assert (
            first.template_name
            == second.template_name
        )

        assert (
            first.sections
            == second.sections
        )