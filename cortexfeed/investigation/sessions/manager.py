# File: cortexfeed/investigation/sessions/manager.py

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .evidence import EvidenceRegistry
from .facts import FactRegistry
from .hypotheses import HypothesisRegistry
from .memory import InvestigationMemory, MemoryStore
from .models import InvestigationSession, SessionMetadata
from .timeline import EventTypes, TimelineStore

EVIDENCE_DIRECTORIES = (
    "files",
    "logs",
    "terminal",
)


class SessionManager:
    """
    Manages investigation session lifecycle.

    Storage:

    data/
    └── sessions/
        └── <project_name>/
            ├── session.json
            ├── memory.json
            ├── facts.json
            ├── hypotheses.json
            ├── timeline.jsonl
            ├── evidence/
            └── prompts/
    """

    SESSION_FILE = "session.json"

    def __init__(
        self,
        sessions_root: Path,
    ) -> None:
        self._sessions_root = sessions_root

    def create_session(
        self,
        project_name: str,
    ) -> InvestigationSession:
        session_directory = (
            self._sessions_root / project_name
        )

        if session_directory.exists():
            raise FileExistsError(
                f"Session already exists: {project_name}"
            )

        session_directory.mkdir(
            parents=True,
        )

        (session_directory / "evidence").mkdir(
            exist_ok=True,
        )

        for directory in EVIDENCE_DIRECTORIES:
            (
                session_directory
                / "evidence"
                / directory
            ).mkdir(exist_ok=True)

        (session_directory / "prompts").mkdir(
            exist_ok=True,
        )

        metadata = SessionMetadata.create(
            project_name=project_name,
        )

        memory = InvestigationMemory()

        memory_store = MemoryStore(
            session_directory,
        )

        facts = FactRegistry(
            session_directory,
        )

        hypotheses = HypothesisRegistry(
            session_directory,
        )

        evidence = EvidenceRegistry(
            session_directory,
        )

        timeline = TimelineStore(
            session_directory,
        )

        self._write_metadata(
            session_directory,
            metadata,
        )

        memory_store.save(memory)
        facts.save()
        hypotheses.save()
        evidence.save()

        timeline.add_event(
            EventTypes.SESSION_CREATED,
            f"Investigation session created for '{project_name}'",
        )

        return InvestigationSession(
            metadata=metadata,
            memory=memory,
            facts=facts,
            hypotheses=hypotheses,
            evidence=evidence,
            timeline=timeline,
            session_directory=session_directory,
        )

    def load_session(
        self,
        project_name: str,
    ) -> InvestigationSession:
        session_directory = (
            self._sessions_root / project_name
        )

        if not session_directory.exists():
            raise FileNotFoundError(
                f"Session not found: {project_name}"
            )

        metadata = self._read_metadata(
            session_directory,
        )

        memory_store = MemoryStore(
            session_directory,
        )

        memory = memory_store.load()

        facts = FactRegistry(
            session_directory,
        )

        facts.load()

        hypotheses = HypothesisRegistry(
            session_directory,
        )

        hypotheses.load()

        evidence = EvidenceRegistry(
            session_directory,
        )

        evidence.load()

        timeline = TimelineStore(
            session_directory,
        )

        timeline.add_event(
            EventTypes.SESSION_LOADED,
            f"Session loaded: {project_name}",
        )

        return InvestigationSession(
            metadata=metadata,
            memory=memory,
            facts=facts,
            hypotheses=hypotheses,
            evidence=evidence,
            timeline=timeline,
            session_directory=session_directory,
        )

    def save_session(
        self,
        session: InvestigationSession,
    ) -> None:
        session.metadata.updated_at = (
            datetime.now(timezone.utc).isoformat()
        )

        self._write_metadata(
            session.session_directory,
            session.metadata,
        )

        memory_store = MemoryStore(
            session.session_directory,
        )

        memory_store.save(
            session.memory,
        )

        session.facts.save()
        session.hypotheses.save()
        session.evidence.save()

        session.timeline.add_event(
            getattr(EventTypes, "SESSION_SAVED", EventTypes.DECISION_MADE),
            "Session saved",
        )

    def delete_session(
        self,
        project_name: str,
    ) -> None:
        session_directory = (
            self._sessions_root / project_name
        )

        if session_directory.exists():
            shutil.rmtree(
                session_directory,
            )

    def list_sessions(
        self,
    ) -> list[SessionMetadata]:
        sessions: list[SessionMetadata] = []

        if not self._sessions_root.exists():
            return sessions

        for directory in sorted(
            self._sessions_root.iterdir()
        ):
            if not directory.is_dir():
                continue

            session_file = (
                directory / self.SESSION_FILE
            )

            if not session_file.exists():
                continue

            try:
                metadata = self._read_metadata(
                    directory,
                )
                sessions.append(metadata)

            except Exception:
                continue

        return sorted(
            sessions,
            key=lambda s: s.updated_at,
            reverse=True,
        )

    def session_exists(
        self,
        project_name: str,
    ) -> bool:
        return (
            self._sessions_root / project_name
        ).exists()

    def get_session_path(
        self,
        project_name: str,
    ) -> Path:
        return (
            self._sessions_root / project_name
        )

    def get_session_stats(
        self,
        session: InvestigationSession,
    ) -> dict[str, int]:
        return {
            "facts": session.facts.count,
            "hypotheses": len(
                session.hypotheses.list()
            ),
            "evidence": len(
                session.evidence.list()
            ),
            "events": session.timeline.count(),
        }

    def _metadata_path(
        self,
        session_directory: Path,
    ) -> Path:
        return (
            session_directory
            / self.SESSION_FILE
        )

    def _write_metadata(
        self,
        session_directory: Path,
        metadata: SessionMetadata,
    ) -> None:
        metadata_path = self._metadata_path(
            session_directory,
        )

        with metadata_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata.to_dict(),
                file,
                indent=2,
                ensure_ascii=False,
            )

    def _read_metadata(
        self,
        session_directory: Path,
    ) -> SessionMetadata:
        metadata_path = self._metadata_path(
            session_directory,
        )

        with metadata_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        return SessionMetadata.from_dict(
            payload,
        )