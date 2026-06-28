# File: cortexfeed/investigation/orchestrator/adapters.py

from __future__ import annotations

from cortexfeed.investigation.analyst.fact_extractor import (
    Evidence as AnalystEvidence,
)
from cortexfeed.investigation.analyst.fact_extractor import (
    Fact as AnalystFact,
)
from cortexfeed.investigation.analyst.hypothesis_engine import (
    Hypothesis as AnalystHypothesis,
)
from cortexfeed.investigation.collector.models import (
    Evidence as CollectorEvidence,
)
from cortexfeed.investigation.sessions.evidence import (
    EvidenceRegistry,
)
from cortexfeed.investigation.sessions.facts import (
    FactRegistry,
)
from cortexfeed.investigation.sessions.hypotheses import (
    HypothesisRegistry,
)

from .exceptions import AdapterError


class FactExtractorEvidenceAdapter:
    """
    Adapts collector evidence into the format expected
    by FactExtractor.
    """

    def adapt(
        self,
        evidence_items: list[CollectorEvidence],
    ) -> list[AnalystEvidence]:
        adapted: list[AnalystEvidence] = []

        for evidence in evidence_items:
            adapted.append(
                AnalystEvidence(
                    id=evidence.evidence_id,
                    source=evidence.source,
                    content=evidence.content,
                    created_at=evidence.collected_at,
                )
            )

        return adapted


class FactAdapter:
    """
    Converts analyst facts into session facts.
    """

    def store(
        self,
        facts: list[AnalystFact],
        registry: FactRegistry,
    ) -> None:
        for fact in facts:
            try:
                registry.add_fact(
                    statement=fact.statement,
                    evidence=fact.evidence_ids,
                )
            except Exception as exc:
                raise AdapterError(
                    f"Failed to store fact '{fact.id}'"
                ) from exc


class HypothesisAdapter:
    """
    Converts analyst hypotheses into
    persisted session hypotheses.
    """

    def store(
        self,
        hypotheses: list[AnalystHypothesis],
        registry: HypothesisRegistry,
    ) -> None:
        existing_statements = {
            hypothesis.statement
            for hypothesis in registry.list()
        }

        for hypothesis in hypotheses:
            if (
                hypothesis.statement
                in existing_statements
            ):
                continue

            try:
                registry.create(
                    statement=hypothesis.statement,
                )
            except Exception as exc:
                raise AdapterError(
                    f"Failed to store hypothesis '{hypothesis.id}'"
                ) from exc


class EvidenceAdapter:
    """
    Stores collector evidence metadata
    inside the session evidence registry.
    """

    def store(
        self,
        evidence_items: list[CollectorEvidence],
        registry: EvidenceRegistry,
    ) -> None:
        for evidence in evidence_items:
            try:
                registry.register(
                    evidence_type=str(
                        evidence.evidence_type
                    ),
                    path=evidence.path or "",
                    metadata={
                        "source": evidence.source,
                    },
                )
            except Exception as exc:
                raise AdapterError(
                    "Failed to store evidence"
                ) from exc


class InvestigationAdapters:
    """
    Central adapter registry.
    """

    def __init__(
        self,
    ) -> None:
        self.fact_extractor_evidence = (
            FactExtractorEvidenceAdapter()
        )

        self.facts = FactAdapter()

        self.hypotheses = (
            HypothesisAdapter()
        )

        self.evidence = (
            EvidenceAdapter()
        )