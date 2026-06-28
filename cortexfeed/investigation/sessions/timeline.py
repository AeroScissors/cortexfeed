# File: cortexfeed/investigation/sessions/timeline.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4


@dataclass(slots=True)
class TimelineEvent:
    """
    Immutable investigation timeline event.

    Timeline is append-only and represents the
    chronological history of an investigation.
    """

    event_id: str
    timestamp: str
    event_type: str
    content: str
    metadata: dict[str, Any]

    @classmethod
    def create(
        cls,
        event_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> "TimelineEvent":
        return cls(
            event_id=f"evt_{uuid4().hex}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            content=content.strip(),
            metadata=metadata or {},
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "TimelineEvent":
        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            content=data["content"],
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventTypes:
    """
    Standard timeline event types.

    Additional types may be added later without
    changing the storage format.
    """

    USER_REQUEST = "user_request"

    EVIDENCE_ADDED = "evidence_added"
    FILE_COLLECTED = "file_collected"
    LOG_COLLECTED = "log_collected"

    QUESTION_ASKED = "question_asked"
    QUESTION_ANSWERED = "question_answered"

    FACT_VERIFIED = "fact_verified"
    HYPOTHESIS_CREATED = "hypothesis_created"
    HYPOTHESIS_DISPROVED = "hypothesis_disproved"

    DECISION_MADE = "decision_made"

    PROMPT_GENERATED = "prompt_generated"

    SESSION_CREATED = "session_created"
    SESSION_LOADED = "session_loaded"


class TimelineStore:
    """
    Append-only timeline persistence.

    Uses JSONL instead of a giant JSON array.

    Benefits:
    - O(1) append operations
    - Efficient for large investigations
    - Supports streaming reads
    - Scales to thousands of events
    """

    FILE_NAME = "timeline.jsonl"

    def __init__(
        self,
        session_directory: Path,
    ) -> None:
        self._session_directory = session_directory
        self._timeline_file = (
            session_directory / self.FILE_NAME
        )

    @property
    def path(self) -> Path:
        return self._timeline_file

    def exists(self) -> bool:
        return self._timeline_file.exists()

    def append(
        self,
        event: TimelineEvent,
    ) -> None:
        self._session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._timeline_file.open(
            mode="a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    event.to_dict(),
                    ensure_ascii=False,
                )
            )
            file.write("\n")

    def add_event(
        self,
        event_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        event = TimelineEvent.create(
            event_type=event_type,
            content=content,
            metadata=metadata,
        )

        self.append(event)

        return event

    def iter_events(self) -> Iterator[TimelineEvent]:
        if not self._timeline_file.exists():
            return

        with self._timeline_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                yield TimelineEvent.from_dict(
                    json.loads(line)
                )

    def list_events(self) -> list[TimelineEvent]:
        return list(self.iter_events())

    def count(self) -> int:
        if not self._timeline_file.exists():
            return 0

        total = 0

        with self._timeline_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for _ in file:
                total += 1

        return total

    def get_recent(
        self,
        limit: int = 100,
    ) -> list[TimelineEvent]:
        events = self.list_events()

        if limit <= 0:
            return []

        return events[-limit:]

    def clear(self) -> None:
        self._session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._timeline_file.write_text(
            "",
            encoding="utf-8",
        )

    def delete(self) -> None:
        if self._timeline_file.exists():
            self._timeline_file.unlink()