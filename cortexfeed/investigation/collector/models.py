# File: cortexfeed/investigation/collector/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class EvidenceType(str, Enum):
    FILE = "FILE"
    FILE_CHUNK = "FILE_CHUNK"

    LOG = "LOG"
    LOG_CHUNK = "LOG_CHUNK"

    TERMINAL = "TERMINAL"

    PROJECT_SUMMARY = "PROJECT_SUMMARY"
    PROJECT_FILE = "PROJECT_FILE"
    
    USER_REPORTED_PROBLEM = "USER_REPORTED_PROBLEM"


@dataclass(slots=True)
class Evidence:
    evidence_id: str
    evidence_type: EvidenceType

    source: str
    path: str | None

    content: str

    collected_at: datetime

    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        evidence_type: EvidenceType,
        source: str,
        content: str,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "Evidence":
        return cls(
            evidence_id=str(uuid4()),
            evidence_type=evidence_type,
            source=source,
            path=path,
            content=content,
            collected_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )


@dataclass(slots=True)
class EvidenceChunk:
    chunk_id: str

    parent_evidence_id: str

    chunk_index: int
    total_chunks: int

    content: str

    start_line: int
    end_line: int

    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        parent_evidence_id: str,
        chunk_index: int,
        total_chunks: int,
        content: str,
        start_line: int,
        end_line: int,
        metadata: dict[str, Any] | None = None,
    ) -> "EvidenceChunk":
        return cls(
            chunk_id=str(uuid4()),
            parent_evidence_id=parent_evidence_id,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            content=content,
            start_line=start_line,
            end_line=end_line,
            metadata=metadata or {},
        )