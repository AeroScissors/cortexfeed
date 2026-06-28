# File: cortexfeed/investigation/sessions/evidence.py

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import EvidenceRecord


class EvidenceTypes:
    FILE = "file"
    LOG = "log"
    TERMINAL = "terminal"
    DOCUMENT = "document"
    SCREENSHOT = "screenshot"


class EvidenceRegistry:
    FILE_NAME = "evidence.json"

    def __init__(
        self,
        session_directory: Path,
    ) -> None:
        self._session_directory = (
            session_directory
        )

        self._file = (
            session_directory
            / self.FILE_NAME
        )

        self._evidence: dict[
            str,
            EvidenceRecord,
        ] = {}

    def register(
        self,
        evidence_type: str,
        path: str,
        file_hash: str | None = None,
        metadata: dict | None = None,
    ) -> EvidenceRecord:
        record = EvidenceRecord(
            evidence_id=f"ev_{uuid4().hex}",
            evidence_type=evidence_type,
            path=path,
            collected_at=datetime.now(
                timezone.utc
            ).isoformat(),
            file_hash=file_hash,
            metadata=metadata or {},
        )

        self._evidence[
            record.evidence_id
        ] = record

        return record

    def get(
        self,
        evidence_id: str,
    ) -> EvidenceRecord | None:
        return self._evidence.get(
            evidence_id
        )

    def list(
        self,
    ) -> list[EvidenceRecord]:
        return sorted(
            self._evidence.values(),
            key=lambda e: e.collected_at,
        )

    def load(self) -> None:
        if not self._file.exists():
            return

        payload = json.loads(
            self._file.read_text(
                encoding="utf-8"
            )
        )

        self._evidence.clear()

        for item in payload.get(
            "evidence",
            [],
        ):
            record = EvidenceRecord(
                **item
            )

            self._evidence[
                record.evidence_id
            ] = record

    def save(self) -> None:
        self._session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "evidence": [
                asdict(record)
                for record in self.list()
            ]
        }

        self._file.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )