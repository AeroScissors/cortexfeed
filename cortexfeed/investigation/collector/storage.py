# File: cortexfeed/investigation/collector/storage.py

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import Evidence, EvidenceChunk


class EvidenceStorage:
    """
    Persists investigation evidence.

    Storage layout:

    data/
        sessions/
            <investigation_id>/
                evidence/
                    evidence.json
                    chunks.json
    """

    def __init__(
        self,
        session_root: str | Path,
    ) -> None:
        self.session_root = Path(session_root)

        self.evidence_dir = (
            self.session_root / "evidence"
        )

        self.evidence_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save_evidence(
        self,
        evidence: list[Evidence],
    ) -> Path:
        path = self.evidence_dir / "evidence.json"

        payload = [
            self._serialize_evidence(item)
            for item in evidence
        ]

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return path

    def save_chunks(
        self,
        chunks: list[EvidenceChunk],
    ) -> Path:
        path = self.evidence_dir / "chunks.json"

        payload = [
            self._serialize_chunk(chunk)
            for chunk in chunks
        ]

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return path

    def load_evidence(
        self,
    ) -> list[Evidence]:
        path = self.evidence_dir / "evidence.json"

        if not path.exists():
            return []

        payload = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

        return [
            self._deserialize_evidence(item)
            for item in payload
        ]

    def load_chunks(
        self,
    ) -> list[EvidenceChunk]:
        path = self.evidence_dir / "chunks.json"

        if not path.exists():
            return []

        payload = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

        return [
            self._deserialize_chunk(item)
            for item in payload
        ]

    def append_evidence(
        self,
        evidence: list[Evidence],
    ) -> None:
        existing = self.load_evidence()
        existing.extend(evidence)

        self.save_evidence(existing)

    def append_chunks(
        self,
        chunks: list[EvidenceChunk],
    ) -> None:
        existing = self.load_chunks()
        existing.extend(chunks)

        self.save_chunks(existing)

    def _serialize_evidence(
        self,
        evidence: Evidence,
    ) -> dict[str, object]:
        data = asdict(evidence)

        data["collected_at"] = (
            evidence.collected_at.isoformat()
        )

        data["evidence_type"] = (
            evidence.evidence_type.value
        )

        return data

    def _serialize_chunk(
        self,
        chunk: EvidenceChunk,
    ) -> dict[str, object]:
        return asdict(chunk)

    def _deserialize_evidence(
        self,
        data: dict[str, object],
    ) -> Evidence:
        return Evidence(
            evidence_id=str(data["evidence_id"]),
            evidence_type=data["evidence_type"],
            source=str(data["source"]),
            path=data.get("path"),
            content=str(data["content"]),
            collected_at=datetime.fromisoformat(
                str(data["collected_at"])
            ),
            metadata=dict(data.get("metadata", {})),
        )

    def _deserialize_chunk(
        self,
        data: dict[str, object],
    ) -> EvidenceChunk:
        return EvidenceChunk(
            chunk_id=str(data["chunk_id"]),
            parent_evidence_id=str(
                data["parent_evidence_id"]
            ),
            chunk_index=int(data["chunk_index"]),
            total_chunks=int(data["total_chunks"]),
            content=str(data["content"]),
            start_line=int(data["start_line"]),
            end_line=int(data["end_line"]),
            metadata=dict(
                data.get("metadata", {})
            ),
        )