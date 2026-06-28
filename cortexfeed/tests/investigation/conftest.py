# File: tests/investigation/conftest.py

from __future__ import annotations

from pathlib import Path

import pytest

from cortexfeed.investigation.core.investigation_service import (
    InvestigationService,
)
from cortexfeed.investigation.facade import (
    CortexFeedInvestigation,
)
from cortexfeed.investigation.orchestrator.engine import (
    InvestigationEngine,
)
from cortexfeed.investigation.sessions.manager import (
    SessionManager,
)


@pytest.fixture
def project_name() -> str:
    return "test-project"


@pytest.fixture
def sample_request() -> str:
    return (
        "Investigate why the backend API "
        "returns HTTP 404 for GET /promise"
    )


@pytest.fixture
def sessions_root(
    tmp_path: Path,
) -> Path:
    root = tmp_path / "sessions"
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def session_manager(
    sessions_root: Path,
) -> SessionManager:
    return SessionManager(
        sessions_root=sessions_root,
    )


@pytest.fixture
def engine(
    sessions_root: Path,
    tmp_path: Path,
) -> InvestigationEngine:
    project_root = tmp_path / "project"
    project_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return InvestigationEngine(
        sessions_root=sessions_root,
        project_root=project_root,
    )


@pytest.fixture
def service(
    sessions_root: Path,
    tmp_path: Path,
) -> InvestigationService:
    project_root = tmp_path / "project"
    project_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return InvestigationService(
        sessions_root=sessions_root,
        project_root=project_root,
    )


@pytest.fixture
def facade(
    sessions_root: Path,
    tmp_path: Path,
) -> CortexFeedInvestigation:
    project_root = tmp_path / "project"
    project_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return CortexFeedInvestigation(
        sessions_root=sessions_root,
        project_root=project_root,
    )


@pytest.fixture
def existing_session(
    session_manager: SessionManager,
    project_name: str,
):
    return session_manager.create_session(
        project_name,
    )