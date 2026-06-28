# File: cortexfeed/investigation/orchestrator/models.py

from __future__ import annotations

from dataclasses import dataclass

from cortexfeed.investigation.planner.models import (
    EvidencePlan,
    InvestigationIntent,
)
from cortexfeed.investigation.prompts.composer import (
    PromptPackage,
)
from cortexfeed.investigation.sessions.models import (
    InvestigationSession,
)


@dataclass(slots=True)
class InvestigationResult:
    """
    Final result produced by the investigation engine.

    Contains both the generated prompt package and
    investigation metadata useful for UI, APIs,
    and future automation layers.
    """

    session: InvestigationSession
    intent: InvestigationIntent
    plan: EvidencePlan
    prompt_package: PromptPackage

    evidence_count: int
    fact_count: int
    hypothesis_count: int
    root_cause: str | None = None
    root_cause_confidence: float = 0.0

    @property
    def project_name(self) -> str:
        return self.session.metadata.project_name

    def to_summary(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "intent": self.intent.investigation_type.value,
            "domain": self.intent.domain.value,
            "confidence": self.intent.confidence,
            "evidence_count": self.evidence_count,
            "fact_count": self.fact_count,
            "hypothesis_count": self.hypothesis_count,
            "root_cause": self.root_cause,
            "root_cause_confidence": self.root_cause_confidence,
            "template": self.prompt_package.template_name,
        }