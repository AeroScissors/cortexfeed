# File: cortexfeed/investigation/orchestrator/coordinator.py

from __future__ import annotations

from cortexfeed.investigation.analyst.fact_extractor import (
    FactExtractor,
)
from cortexfeed.investigation.analyst.hypothesis_engine import (
    HypothesisEngine,
)
from cortexfeed.investigation.analyst.root_cause import (
    RootCauseAnalyzer,
)

from cortexfeed.investigation.collector.models import (
    Evidence,
    EvidenceType,
)
from cortexfeed.investigation.planner.evidence_planner import (
    EvidencePlanner,
)
from cortexfeed.investigation.planner.intent_analyzer import (
    IntentClassifier,
    RuleBasedIntentClassifier,
)
from cortexfeed.investigation.planner.models import (
    EvidencePlan,
    InvestigationIntent,
    QuestionBundle,
)
from cortexfeed.investigation.planner.question_generator import (
    TemplateQuestionStrategy,
)
from cortexfeed.investigation.prompts.composer import (
    PromptComposer,
    PromptPackage,
)
from cortexfeed.investigation.sessions.manager import (
    SessionManager,
)
from cortexfeed.investigation.sessions.models import (
    InvestigationSession,
)

from .adapters import (
    InvestigationAdapters,
)
from .collector_coordinator import (
    CollectorCoordinator,
)
from .exceptions import (
    AnalysisError,
    CollectionError,
    PersistenceError,
    PlanningError,
    PromptGenerationError,
)


class InvestigationCoordinator:
    """
    Central orchestration workflow.

    Coordinates:

    Intent Analysis
        ↓
    Evidence Planning
        ↓
    Question Generation
        ↓
    Evidence Collection
        ↓
    Fact Extraction
        ↓
    Hypothesis Generation
        ↓
    Session Persistence
        ↓
    Prompt Composition
    """

    def __init__(
        self,
        *,
        session_manager: SessionManager,
        collector_coordinator: CollectorCoordinator,
        intent_classifier: IntentClassifier | None = None,
        evidence_planner: EvidencePlanner | None = None,
        question_generator: TemplateQuestionStrategy | None = None,
        fact_extractor: FactExtractor | None = None,
        hypothesis_engine: HypothesisEngine | None = None,
        root_cause_analyzer: RootCauseAnalyzer | None = None,
        prompt_composer: PromptComposer | None = None,
        adapters: InvestigationAdapters | None = None,
    ) -> None:
        self.session_manager = session_manager

        self.intent_classifier = (
            intent_classifier
            or RuleBasedIntentClassifier()
        )

        self.evidence_planner = (
            evidence_planner
            or EvidencePlanner()
        )

        self.question_generator = (
            question_generator
            or TemplateQuestionStrategy()
        )

        self.collector_coordinator = (
            collector_coordinator
        )

        self.fact_extractor = (
            fact_extractor
            or FactExtractor()
        )

        self.hypothesis_engine = (
            hypothesis_engine
            or HypothesisEngine()
        )

        self.root_cause_analyzer = (
            root_cause_analyzer
            or RootCauseAnalyzer()
        )

        self.prompt_composer = (
            prompt_composer
            or PromptComposer()
        )

        self.adapters = (
            adapters
            or InvestigationAdapters()
        )

    def analyze_intent(
        self,
        request: str,
    ) -> InvestigationIntent:
        try:
            return self.intent_classifier.classify(
                request,
            )

        except Exception as exc:
            raise PlanningError(
                "Intent analysis failed."
            ) from exc

    def create_plan(
        self,
        intent: InvestigationIntent,
    ) -> EvidencePlan:
        try:
            return self.evidence_planner.create_plan(
                intent,
            )

        except Exception as exc:
            raise PlanningError(
                "Evidence planning failed."
            ) from exc

    def generate_questions(
        self,
        plan: EvidencePlan,
    ) -> QuestionBundle:
        try:
            return self.question_generator.generate(
                plan,
            )

        except Exception as exc:
            raise PlanningError(
                "Question generation failed."
            ) from exc

    def collect_evidence(
        self,
        plan: EvidencePlan,
    ) -> list[Evidence]:
        try:
            return self.collector_coordinator.collect(
                plan,
            )

        except Exception as exc:
            raise CollectionError(
                f"Evidence collection failed: {type(exc).__name__}: {exc}"
            ) from exc

    def analyze_evidence(
        self,
        request: str,
        evidence: list[Evidence],
        session: InvestigationSession,
    ) -> None:
        try:
            request_evidence = Evidence.create(
                evidence_type=EvidenceType.USER_REPORTED_PROBLEM,
                source="investigation_request",
                content=request,
                metadata={
                    "source": "user_request",
                },
            )

            all_evidence = [
                request_evidence,
                *evidence,
            ]

            adapted_evidence = (
                self.adapters.fact_extractor_evidence.adapt(
                    all_evidence,
                )
            )

            facts = self.fact_extractor.extract(
                adapted_evidence,
            )

            self.adapters.facts.store(
                facts,
                session.facts,
            )

            hypotheses = (
                self.hypothesis_engine.generate(
                    facts,
                )
            )

            root_cause = (
                self.root_cause_analyzer.analyze(
                    hypotheses,
                )
            )
            
            session.memory.add_decision(
                f"Root Cause: {root_cause.likely_root_cause}"
            )

            hypotheses = (
                self.hypothesis_engine.update_status(
                    hypotheses,
                )
            )

            self.adapters.hypotheses.store(
                hypotheses,
                session.hypotheses,
            )

            self.adapters.evidence.store(
                all_evidence,
                session.evidence,
            )

        except Exception as exc:
            raise AnalysisError(
                "Evidence analysis failed."
            ) from exc

    # Event types that are meaningful to show in the prompt.
    # Everything else (session_loaded, session_saved,
    # prompt_generated, session_created) is operational
    # noise and must be excluded.
    _SIGNAL_EVENT_TYPES = frozenset({
        "user_request",
        "decision_made",
        "fact_verified",
        "hypothesis_created",
        "evidence_added",
    })

    # Facts longer than this are almost certainly raw
    # conversation dumps, not extracted observations.
    _MAX_FACT_LENGTH = 350

    def compose_prompt(
        self,
        *,
        session: InvestigationSession,
        request: str,
    ) -> PromptPackage:
        try:
            # ── Facts ────────────────────────────────────────
            # Skip raw conversation dumps (very long strings or
            # strings that begin with a chat-turn prefix).
            facts = [
                fact.statement
                for fact in session.facts.list_facts()
                if len(fact.statement) <= self._MAX_FACT_LENGTH
                and not fact.statement.startswith("[USER]:")
            ]

            # ── Hypotheses ───────────────────────────────────
            hypotheses = [
                hypothesis.statement
                for hypothesis in session.hypotheses.list()
            ]

            # ── Evidence ────────────────────────────────────
            # Only include records that actually have a file path.
            # Records created from user-reported problems have an
            # empty path and produce blank bullets in the prompt.
            evidence = [
                ev.path
                for ev in session.evidence.list()
                if ev.path
            ]

            # ── Timeline ─────────────────────────────────────
            # Keep only signal events (user requests, decisions,
            # findings). Deduplicate by content prefix so the
            # same request doesn't appear 10 times across reruns.
            seen: set[str] = set()
            timeline: list[str] = []
            for event in session.timeline.list_events():
                if event.event_type not in self._SIGNAL_EVENT_TYPES:
                    continue
                dedup_key = event.content[:80]
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                timeline.append(event.content)

            return self.prompt_composer.compose(
                project=session.metadata.project_name,
                current_issue=request,
                facts=facts,
                hypotheses=hypotheses,
                evidence=evidence,
                timeline=timeline,
                task=request,
            )

        except Exception as exc:
            raise PromptGenerationError(
                "Prompt generation failed."
            ) from exc

    def persist_session(
        self,
        session: InvestigationSession,
    ) -> None:
        try:
            self.session_manager.save_session(
                session,
            )

        except Exception as exc:
            raise PersistenceError(
                "Session persistence failed."
            ) from exc