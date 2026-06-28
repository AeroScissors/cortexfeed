# File: cortexfeed/investigation/sessions/hypotheses.py

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import Hypothesis


class HypothesisStatus:
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    DISPROVED = "disproved"


class HypothesisRegistry:
    FILE_NAME = "hypotheses.json"

    def __init__(
        self,
        session_directory: Path,
    ) -> None:
        self._session_directory = session_directory
        self._file = (
            session_directory / self.FILE_NAME
        )

        self._hypotheses: dict[str, Hypothesis] = {}

    def create(
        self,
        statement: str,
    ) -> Hypothesis:
        hypothesis = Hypothesis(
            hypothesis_id=f"hyp_{uuid4().hex}",
            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),
            statement=statement.strip(),
            status=HypothesisStatus.ACTIVE,
        )

        self._hypotheses[
            hypothesis.hypothesis_id
        ] = hypothesis

        return hypothesis

    def get(
        self,
        hypothesis_id: str,
    ) -> Hypothesis | None:
        return self._hypotheses.get(
            hypothesis_id
        )

    def list(
        self,
    ) -> list[Hypothesis]:
        return sorted(
            self._hypotheses.values(),
            key=lambda h: h.timestamp,
        )

    def confirm(
        self,
        hypothesis_id: str,
    ) -> None:
        hypothesis = self._hypotheses[
            hypothesis_id
        ]

        hypothesis.status = (
            HypothesisStatus.CONFIRMED
        )

    def disprove(
        self,
        hypothesis_id: str,
    ) -> None:
        hypothesis = self._hypotheses[
            hypothesis_id
        ]

        hypothesis.status = (
            HypothesisStatus.DISPROVED
        )

    def load(self) -> None:
        if not self._file.exists():
            return

        payload = json.loads(
            self._file.read_text(
                encoding="utf-8"
            )
        )

        self._hypotheses.clear()

        for item in payload.get(
            "hypotheses",
            [],
        ):
            hypothesis = Hypothesis(**item)

            self._hypotheses[
                hypothesis.hypothesis_id
            ] = hypothesis

    def save(self) -> None:
        self._session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "hypotheses": [
                asdict(h)
                for h in self.list()
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