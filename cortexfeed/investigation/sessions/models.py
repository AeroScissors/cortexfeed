# File: cortexfeed/investigation/sessions/models.py

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .evidence import EvidenceRegistry
    from .facts import FactRegistry
    from .hypotheses import HypothesisRegistry
    from .memory import InvestigationMemory
    from .timeline import TimelineStore


@dataclass(slots=True)
class SessionMetadata:
    """
    High-level metadata describing an investigation session.
    """

    project_name: str
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        project_name: str,
    ) -> "SessionMetadata":
        now = datetime.now(timezone.utc).isoformat()

        return cls(
            project_name=project_name,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "SessionMetadata":
        return cls(
            project_name=data["project_name"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class EvidenceRecord:
    """
    Persistence model for collected evidence.
    """

    evidence_id: str
    evidence_type: str
    path: str
    collected_at: str
    file_hash: str | None
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Hypothesis:
    """
    Persistence model for session-level hypothesis state.
    Distinct from the Analyst Hypothesis (which contains reasoning/scores).
    """

    hypothesis_id: str
    timestamp: str
    statement: str
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class InvestigationSession:
    """
    Aggregate root for an investigation session.
    """

    metadata: SessionMetadata
    memory: InvestigationMemory
    facts: FactRegistry
    hypotheses: HypothesisRegistry
    evidence: EvidenceRegistry
    timeline: TimelineStore
    session_directory: Path