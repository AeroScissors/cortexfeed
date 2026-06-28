# File: tests/investigation/test_investigation.py

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cortexfeed.investigation.sessions.manager import (
    SessionManager,
)

class TestSessionLifecycle:
    def test_create_session(
        self,
        session_manager: SessionManager,
        project_name: str,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        assert (
            session.metadata.project_name
            == project_name
        )

        assert session.session_directory.exists()

        assert (
            session.session_directory
            / "session.json"
        ).exists()

        assert (
            session.session_directory
            / "memory.json"
        ).exists()

        assert (
            session.session_directory
            / "facts.json"
        ).exists()

        assert (
            session.session_directory
            / "hypotheses.json"
        ).exists()

        assert (
            session.session_directory
            / "evidence"
        ).exists()

        assert (
            session.session_directory
            / "prompts"
        ).exists()

    def test_session_exists_after_create(
        self,
        session_manager: SessionManager,
        project_name: str,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        assert session_manager.session_exists(
            project_name,
        )

    def test_load_session(
        self,
        session_manager: SessionManager,
        project_name: str,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        loaded = session_manager.load_session(
            project_name,
        )

        assert (
            loaded.metadata.project_name
            == project_name
        )

        assert loaded.session_directory.exists()

    def test_save_session_updates_metadata(
        self,
        existing_session,
    ) -> None:
        previous_timestamp = (
            existing_session.metadata.updated_at
        )

        
        existing_session.timeline.add_event(
            "test",
            "save validation",
        )

        existing_session.metadata.updated_at = (
            "2000-01-01T00:00:00"
        )

        manager = SessionManager(
            existing_session.session_directory.parent,
        )

        manager.save_session(
            existing_session,
        )

        assert (
            existing_session.metadata.updated_at
            != previous_timestamp
        )

    def test_list_sessions_returns_created_session(
        self,
        session_manager: SessionManager,
        project_name: str,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        sessions = (
            session_manager.list_sessions()
        )

        assert len(sessions) == 1

        assert (
            sessions[0].project_name
            == project_name
        )

    def test_delete_session(
        self,
        session_manager: SessionManager,
        project_name: str,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        assert session_manager.session_exists(
            project_name,
        )

        session_manager.delete_session(
            project_name,
        )

        assert not session_manager.session_exists(
            project_name,
        )

    def test_get_session_path(
        self,
        session_manager: SessionManager,
        project_name: str,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        path = session_manager.get_session_path(
            project_name,
        )

        assert isinstance(
            path,
            Path,
        )

        assert path.exists()

    def test_get_session_stats(
        self,
        existing_session,
    ) -> None:
        manager = SessionManager(
            existing_session.session_directory.parent,
        )

        stats = manager.get_session_stats(
            existing_session,
        )

        assert isinstance(
            stats,
            dict,
        )

        assert "facts" in stats
        assert "hypotheses" in stats
        assert "evidence" in stats
        assert "events" in stats

    def test_load_missing_session_raises(
        self,
        session_manager: SessionManager,
    ) -> None:
        import pytest

        with pytest.raises(
            FileNotFoundError,
        ):
            session_manager.load_session(
                "missing-project",
            )

    def test_duplicate_session_creation_raises(
        self,
        session_manager: SessionManager,
        project_name: str,
    ) -> None:
        import pytest

        session_manager.create_session(
            project_name,
        )

        with pytest.raises(
            FileExistsError,
        ):
            session_manager.create_session(
                project_name,
            )








# File: tests/investigation/test_investigation.py

from unittest.mock import MagicMock

import pytest

from cortexfeed.investigation.orchestrator.exceptions import (
    InvalidInvestigationRequestError,
    SessionResolutionError,
)


class TestEngineContracts:
    def test_empty_request_rejected(
        self,
        engine,
    ) -> None:
        with pytest.raises(
            InvalidInvestigationRequestError,
        ):
            engine.investigate(
                "",
                project_name="test-project",
            )

    def test_whitespace_request_rejected(
        self,
        engine,
    ) -> None:
        with pytest.raises(
            InvalidInvestigationRequestError,
        ):
            engine.investigate(
                "    ",
                project_name="test-project",
            )

    def test_resume_returns_existing_session(
        self,
        session_manager,
        project_name,
        engine,
    ) -> None:
        created = (
            session_manager.create_session(
                project_name,
            )
        )

        loaded = engine.resume(
            project_name=project_name,
        )

        assert (
            loaded.metadata.project_name
            == created.metadata.project_name
        )

    def test_session_exists_for_existing_project(
        self,
        session_manager,
        project_name,
        engine,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        assert engine.session_exists(
            project_name,
        )

    def test_session_not_exists_for_missing_project(
        self,
        engine,
    ) -> None:
        assert (
            engine.session_exists(
                "missing-project"
            )
            is False
        )

    def test_list_sessions_returns_created_session(
        self,
        session_manager,
        project_name,
        engine,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        sessions = engine.list_sessions()

        assert len(sessions) == 1

        assert (
            sessions[0].project_name
            == project_name
        )

    def test_investigation_creates_new_session(
        self,
        monkeypatch,
        engine,
    ) -> None:
        fake_session = (
            engine.session_manager.create_session(
                "demo-project"
            )
        )

        fake_intent = MagicMock()
        fake_plan = MagicMock()
        fake_prompt = MagicMock()

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: fake_session,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            lambda request: fake_intent,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "create_plan",
            lambda intent: fake_plan,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "generate_questions",
            lambda plan: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "collect_evidence",
            lambda plan: [],
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_evidence",
            lambda request, evidence, session: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "compose_prompt",
            lambda **kwargs: fake_prompt,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "persist_session",
            lambda session: None,
        )

        result = engine.investigate(
            "debug backend route",
            project_name="demo-project",
        )

        assert result.session is fake_session
        assert result.intent is fake_intent
        assert result.plan is fake_plan
        assert result.prompt_package is fake_prompt

    def test_investigation_adds_user_request_event(
        self,
        monkeypatch,
        engine,
    ) -> None:
        session = (
            engine.session_manager.create_session(
                "timeline-project"
            )
        )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: session,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            lambda request: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "create_plan",
            lambda intent: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "generate_questions",
            lambda plan: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "collect_evidence",
            lambda plan: [],
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_evidence",
            lambda request, evidence, session: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "compose_prompt",
            lambda **kwargs: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "persist_session",
            lambda session: None,
        )

        engine.investigate(
            "find root cause",
            project_name="timeline-project",
        )

        events = session.timeline.list_events()

        assert len(events) > 0

    def test_session_resolution_failure_propagates(
        self,
        monkeypatch,
        engine,
    ) -> None:
        def raise_error(*args, **kwargs):
            raise SessionResolutionError(
                "failed"
            )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            raise_error,
        )

        with pytest.raises(
            SessionResolutionError,
        ):
            engine.investigate(
                "debug api",
                project_name="broken",
            )










class TestFailurePropagation:
    def test_intent_analysis_failure(
        self,
        monkeypatch,
        engine,
    ) -> None:
        from cortexfeed.investigation.orchestrator.exceptions import (
            PlanningError,
        )

        session = (
            engine.session_manager.create_session(
                "intent-failure"
            )
        )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: session,
        )

        def raise_error(*args, **kwargs):
            raise PlanningError(
                "intent failed"
            )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            raise_error,
        )

        with pytest.raises(
            PlanningError,
        ):
            engine.investigate(
                "debug backend",
                project_name="intent-failure",
            )

    def test_plan_generation_failure(
        self,
        monkeypatch,
        engine,
    ) -> None:
        from cortexfeed.investigation.orchestrator.exceptions import (
            PlanningError,
        )

        session = (
            engine.session_manager.create_session(
                "plan-failure"
            )
        )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: session,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            lambda request: MagicMock(),
        )

        def raise_error(*args, **kwargs):
            raise PlanningError(
                "planning failed"
            )

        monkeypatch.setattr(
            engine.coordinator,
            "create_plan",
            raise_error,
        )

        with pytest.raises(
            PlanningError,
        ):
            engine.investigate(
                "debug backend",
                project_name="plan-failure",
            )

    def test_collection_failure(
        self,
        monkeypatch,
        engine,
    ) -> None:
        from cortexfeed.investigation.orchestrator.exceptions import (
            CollectionError,
        )

        session = (
            engine.session_manager.create_session(
                "collection-failure"
            )
        )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: session,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            lambda request: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "create_plan",
            lambda intent: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "generate_questions",
            lambda plan: None,
        )

        def raise_error(*args, **kwargs):
            raise CollectionError(
                "collection failed"
            )

        monkeypatch.setattr(
            engine.coordinator,
            "collect_evidence",
            raise_error,
        )

        with pytest.raises(
            CollectionError,
        ):
            engine.investigate(
                "debug backend",
                project_name="collection-failure",
            )

    def test_analysis_failure(
        self,
        monkeypatch,
        engine,
    ) -> None:
        from cortexfeed.investigation.orchestrator.exceptions import (
            AnalysisError,
        )

        session = (
            engine.session_manager.create_session(
                "analysis-failure"
            )
        )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: session,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            lambda request: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "create_plan",
            lambda intent: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "generate_questions",
            lambda plan: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "collect_evidence",
            lambda plan: [],
        )

        def raise_error(*args, **kwargs):
            raise AnalysisError(
                "analysis failed"
            )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_evidence",
            raise_error,
        )

        with pytest.raises(
            AnalysisError,
        ):
            engine.investigate(
                "debug backend",
                project_name="analysis-failure",
            )

    def test_prompt_generation_failure(
        self,
        monkeypatch,
        engine,
    ) -> None:
        from cortexfeed.investigation.orchestrator.exceptions import (
            PromptGenerationError,
        )

        session = (
            engine.session_manager.create_session(
                "prompt-failure"
            )
        )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: session,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            lambda request: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "create_plan",
            lambda intent: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "generate_questions",
            lambda plan: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "collect_evidence",
            lambda plan: [],
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_evidence",
            lambda request, evidence, session: None,
        )

        def raise_error(*args, **kwargs):
            raise PromptGenerationError(
                "prompt failed"
            )

        monkeypatch.setattr(
            engine.coordinator,
            "compose_prompt",
            raise_error,
        )

        with pytest.raises(
            PromptGenerationError,
        ):
            engine.investigate(
                "debug backend",
                project_name="prompt-failure",
            )

    def test_persistence_failure(
        self,
        monkeypatch,
        engine,
    ) -> None:
        from cortexfeed.investigation.orchestrator.exceptions import (
            PersistenceError,
        )

        session = (
            engine.session_manager.create_session(
                "persistence-failure"
            )
        )

        monkeypatch.setattr(
            engine,
            "_resolve_session",
            lambda project_name: session,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_intent",
            lambda request: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "create_plan",
            lambda intent: MagicMock(),
        )

        monkeypatch.setattr(
            engine.coordinator,
            "generate_questions",
            lambda plan: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "collect_evidence",
            lambda plan: [],
        )

        monkeypatch.setattr(
            engine.coordinator,
            "analyze_evidence",
            lambda request, evidence, session: None,
        )

        monkeypatch.setattr(
            engine.coordinator,
            "compose_prompt",
            lambda **kwargs: MagicMock(),
        )

        def raise_error(*args, **kwargs):
            raise PersistenceError(
                "save failed"
            )

        monkeypatch.setattr(
            engine.coordinator,
            "persist_session",
            raise_error,
        )

        with pytest.raises(
            PersistenceError,
        ):
            engine.investigate(
                "debug backend",
                project_name="persistence-failure",
            )








class TestServiceContracts:
    def test_service_investigate_delegates_to_engine(
        self,
        monkeypatch,
        service,
    ) -> None:
        expected = MagicMock()

        def fake_investigate(
            self,
            *,
            request,
            project_name,
        ):
            return expected

        monkeypatch.setattr(
            "cortexfeed.investigation.orchestrator.engine.InvestigationEngine.investigate",
            fake_investigate,
        )

        result = service.investigate(
            request="debug backend",
            project_name="service-project",
        )

        assert result is expected

    def test_service_generate_prompt(
        self,
        monkeypatch,
        service,
    ) -> None:
        package = MagicMock()

        result = MagicMock()
        result.prompt_package = package

        monkeypatch.setattr(
            service,
            "investigate",
            lambda **kwargs: result,
        )

        monkeypatch.setattr(
            service._formatter,
            "format",
            lambda package: "FORMATTED PROMPT",
        )

        prompt = service.generate_prompt(
            request="debug backend",
            project_name="service-project",
        )

        assert prompt == "FORMATTED PROMPT"

    def test_service_resume(
        self,
        monkeypatch,
        service,
    ) -> None:
        expected_session = MagicMock()

        monkeypatch.setattr(
            "cortexfeed.investigation.orchestrator.engine.InvestigationEngine.resume",
            lambda self, *, project_name: expected_session,
        )

        session = service.resume(
            project_name="resume-project",
        )

        assert session is expected_session

    def test_service_list_sessions(
        self,
        monkeypatch,
        service,
    ) -> None:
        expected = [
            MagicMock(),
            MagicMock(),
        ]

        monkeypatch.setattr(
            "cortexfeed.investigation.orchestrator.engine.InvestigationEngine.list_sessions",
            lambda self: expected,
        )

        sessions = service.list_sessions()

        assert sessions == expected

    def test_service_session_exists_true(
        self,
        monkeypatch,
        service,
    ) -> None:
        monkeypatch.setattr(
            "cortexfeed.investigation.orchestrator.engine.InvestigationEngine.session_exists",
            lambda self, project_name: True,
        )

        assert service.session_exists(
            "demo"
        )

    def test_service_session_exists_false(
        self,
        monkeypatch,
        service,
    ) -> None:
        monkeypatch.setattr(
            "cortexfeed.investigation.orchestrator.engine.InvestigationEngine.session_exists",
            lambda self, project_name: False,
        )

        assert (
            service.session_exists(
                "demo"
            )
            is False
        )

    def test_service_summary(
        self,
        service,
    ) -> None:
        result = MagicMock()

        expected_summary = {
            "project_name": "demo",
            "fact_count": 3,
        }

        result.to_summary.return_value = (
            expected_summary
        )

        summary = service.summarize(
            result,
        )

        assert summary == expected_summary

    def test_service_generate_prompt_passes_arguments(
        self,
        monkeypatch,
        service,
    ) -> None:
        captured = {}

        def fake_investigate(
            **kwargs,
        ):
            captured.update(kwargs)

            result = MagicMock()
            result.prompt_package = (
                MagicMock()
            )
            return result

        monkeypatch.setattr(
            service,
            "investigate",
            fake_investigate,
        )

        monkeypatch.setattr(
            service._formatter,
            "format",
            lambda package: "PROMPT",
        )

        service.generate_prompt(
            request="debug api",
            project_name="trust-ledger",
        )

        assert (
            captured["request"]
            == "debug api"
        )

        assert (
            captured["project_name"]
            == "trust-ledger"
        )

    def test_service_formatter_called(
        self,
        monkeypatch,
        service,
    ) -> None:
        result = MagicMock()
        result.prompt_package = (
            MagicMock()
        )

        formatter_called = False

        monkeypatch.setattr(
            service,
            "investigate",
            lambda **kwargs: result,
        )

        def fake_format(package):
            nonlocal formatter_called
            formatter_called = True
            return "prompt"

        monkeypatch.setattr(
            service._formatter,
            "format",
            fake_format,
        )

        service.generate_prompt(
            request="debug",
            project_name="demo",
        )

        assert formatter_called










class TestFacadeContracts:
    def test_facade_investigate_delegates_to_service(
        self,
        monkeypatch,
        facade,
    ) -> None:
        expected = MagicMock()

        monkeypatch.setattr(
            facade._service,
            "investigate",
            lambda **kwargs: expected,
        )

        result = facade.investigate(
            request="debug backend",
            project_name="demo",
        )

        assert result is expected

    def test_facade_generate_prompt(
        self,
        monkeypatch,
        facade,
    ) -> None:
        monkeypatch.setattr(
            facade._service,
            "generate_prompt",
            lambda **kwargs: "PROMPT",
        )

        result = facade.generate_prompt(
            request="debug backend",
            project_name="demo",
        )

        assert result == "PROMPT"

    def test_facade_resume(
        self,
        monkeypatch,
        facade,
    ) -> None:
        expected_session = MagicMock()

        monkeypatch.setattr(
            facade._service,
            "resume",
            lambda **kwargs: expected_session,
        )

        session = facade.resume(
            project_name="demo",
        )

        assert session is expected_session

    def test_facade_list_sessions(
        self,
        monkeypatch,
        facade,
    ) -> None:
        expected = [
            MagicMock(),
            MagicMock(),
        ]

        monkeypatch.setattr(
            facade._service,
            "list_sessions",
            lambda: expected,
        )

        sessions = facade.list_sessions()

        assert sessions == expected

    def test_facade_session_exists_true(
        self,
        monkeypatch,
        facade,
    ) -> None:
        monkeypatch.setattr(
            facade._service,
            "session_exists",
            lambda project_name: True,
        )

        assert facade.session_exists(
            "demo"
        )

    def test_facade_session_exists_false(
        self,
        monkeypatch,
        facade,
    ) -> None:
        monkeypatch.setattr(
            facade._service,
            "session_exists",
            lambda project_name: False,
        )

        assert (
            facade.session_exists(
                "demo"
            )
            is False
        )

    def test_facade_summary(
        self,
        monkeypatch,
        facade,
    ) -> None:
        expected = {
            "project_name": "demo",
            "fact_count": 5,
        }

        monkeypatch.setattr(
            facade._service,
            "summarize",
            lambda result: expected,
        )

        summary = facade.summarize(
            MagicMock(),
        )

        assert summary == expected

    def test_facade_investigate_passes_request(
        self,
        monkeypatch,
        facade,
    ) -> None:
        captured = {}

        def fake_investigate(
            **kwargs,
        ):
            captured.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(
            facade._service,
            "investigate",
            fake_investigate,
        )

        facade.investigate(
            request="debug api route",
            project_name="trust-ledger",
        )

        assert (
            captured["request"]
            == "debug api route"
        )

        assert (
            captured["project_name"]
            == "trust-ledger"
        )

    def test_facade_generate_prompt_passes_arguments(
        self,
        monkeypatch,
        facade,
    ) -> None:
        captured = {}

        def fake_prompt(
            **kwargs,
        ):
            captured.update(kwargs)
            return "PROMPT"

        monkeypatch.setattr(
            facade._service,
            "generate_prompt",
            fake_prompt,
        )

        facade.generate_prompt(
            request="investigate auth",
            project_name="backend",
        )

        assert (
            captured["request"]
            == "investigate auth"
        )

        assert (
            captured["project_name"]
            == "backend"
        )

    def test_facade_returns_service_result_unchanged(
        self,
        monkeypatch,
        facade,
    ) -> None:
        expected = MagicMock()

        monkeypatch.setattr(
            facade._service,
            "investigate",
            lambda **kwargs: expected,
        )

        result = facade.investigate(
            request="debug",
            project_name="demo",
        )

        assert result is expected















class TestPersistenceContracts:
    def test_session_directory_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        assert (
            session.session_directory.exists()
        )

        assert (
            session.session_directory.is_dir()
        )

    def test_metadata_file_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        metadata_file = (
            session.session_directory
            / "session.json"
        )

        assert metadata_file.exists()

    def test_evidence_directories_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        evidence_root = (
            session.session_directory
            / "evidence"
        )

        assert evidence_root.exists()

        assert (
            evidence_root
            / "files"
        ).exists()

        assert (
            evidence_root
            / "logs"
        ).exists()

        assert (
            evidence_root
            / "terminal"
        ).exists()

    def test_prompts_directory_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        prompts_dir = (
            session.session_directory
            / "prompts"
        )

        assert prompts_dir.exists()

    def test_save_load_roundtrip(
        self,
        session_manager,
        project_name,
    ) -> None:
        created = (
            session_manager.create_session(
                project_name,
            )
        )

        session_manager.save_session(
            created,
        )

        loaded = (
            session_manager.load_session(
                project_name,
            )
        )

        assert (
            loaded.metadata.project_name
            == created.metadata.project_name
        )

    def test_saved_metadata_persists(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        session_manager.save_session(
            session,
        )

        loaded = (
            session_manager.load_session(
                project_name,
            )
        )

        assert (
            loaded.metadata.project_name
            == project_name
        )

    def test_session_delete_removes_directory(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        path = (
            session.session_directory
        )

        assert path.exists()

        session_manager.delete_session(
            project_name,
        )

        assert not path.exists()

    def test_list_sessions_contains_saved_session(
        self,
        session_manager,
    ) -> None:
        session_manager.create_session(
            "project-a",
        )

        session_manager.create_session(
            "project-b",
        )

        sessions = (
            session_manager.list_sessions()
        )

        names = {
            session.project_name
            for session in sessions
        }

        assert "project-a" in names
        assert "project-b" in names

    def test_session_stats_contract(
        self,
        existing_session,
        session_manager,
    ) -> None:
        stats = (
            session_manager.get_session_stats(
                existing_session,
            )
        )

        assert isinstance(
            stats,
            dict,
        )

        assert (
            set(stats.keys())
            == {
                "facts",
                "hypotheses",
                "evidence",
                "events",
            }
        )

    def test_session_path_contract(
        self,
        session_manager,
        project_name,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        path = (
            session_manager.get_session_path(
                project_name,
            )
        )

        assert path.name == project_name

    def test_session_exists_after_save(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        session_manager.save_session(
            session,
        )

        assert (
            session_manager.session_exists(
                project_name,
            )
        )

    def test_session_not_exists_after_delete(
        self,
        session_manager,
        project_name,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        session_manager.delete_session(
            project_name,
        )

        assert (
            session_manager.session_exists(
                project_name,
            )
            is False
        )

    def test_load_after_save_preserves_directory(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        original_dir = (
            session.session_directory
        )

        session_manager.save_session(
            session,
        )

        loaded = (
            session_manager.load_session(
                project_name,
            )
        )

        assert (
            loaded.session_directory
            == original_dir
        )




















class TestPersistenceContracts:
    def test_session_directory_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        assert (
            session.session_directory.exists()
        )

        assert (
            session.session_directory.is_dir()
        )

    def test_metadata_file_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        metadata_file = (
            session.session_directory
            / "session.json"
        )

        assert metadata_file.exists()

    def test_evidence_directories_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        evidence_root = (
            session.session_directory
            / "evidence"
        )

        assert evidence_root.exists()

        assert (
            evidence_root
            / "files"
        ).exists()

        assert (
            evidence_root
            / "logs"
        ).exists()

        assert (
            evidence_root
            / "terminal"
        ).exists()

    def test_prompts_directory_created(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = session_manager.create_session(
            project_name,
        )

        prompts_dir = (
            session.session_directory
            / "prompts"
        )

        assert prompts_dir.exists()

    def test_save_load_roundtrip(
        self,
        session_manager,
        project_name,
    ) -> None:
        created = (
            session_manager.create_session(
                project_name,
            )
        )

        session_manager.save_session(
            created,
        )

        loaded = (
            session_manager.load_session(
                project_name,
            )
        )

        assert (
            loaded.metadata.project_name
            == created.metadata.project_name
        )

    def test_saved_metadata_persists(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        session_manager.save_session(
            session,
        )

        loaded = (
            session_manager.load_session(
                project_name,
            )
        )

        assert (
            loaded.metadata.project_name
            == project_name
        )

    def test_session_delete_removes_directory(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        path = (
            session.session_directory
        )

        assert path.exists()

        session_manager.delete_session(
            project_name,
        )

        assert not path.exists()

    def test_list_sessions_contains_saved_session(
        self,
        session_manager,
    ) -> None:
        session_manager.create_session(
            "project-a",
        )

        session_manager.create_session(
            "project-b",
        )

        sessions = (
            session_manager.list_sessions()
        )

        names = {
            session.project_name
            for session in sessions
        }

        assert "project-a" in names
        assert "project-b" in names

    def test_session_stats_contract(
        self,
        existing_session,
        session_manager,
    ) -> None:
        stats = (
            session_manager.get_session_stats(
                existing_session,
            )
        )

        assert isinstance(
            stats,
            dict,
        )

        assert (
            set(stats.keys())
            == {
                "facts",
                "hypotheses",
                "evidence",
                "events",
            }
        )

    def test_session_path_contract(
        self,
        session_manager,
        project_name,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        path = (
            session_manager.get_session_path(
                project_name,
            )
        )

        assert path.name == project_name

    def test_session_exists_after_save(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        session_manager.save_session(
            session,
        )

        assert (
            session_manager.session_exists(
                project_name,
            )
        )

    def test_session_not_exists_after_delete(
        self,
        session_manager,
        project_name,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        session_manager.delete_session(
            project_name,
        )

        assert (
            session_manager.session_exists(
                project_name,
            )
            is False
        )

    def test_load_after_save_preserves_directory(
        self,
        session_manager,
        project_name,
    ) -> None:
        session = (
            session_manager.create_session(
                project_name,
            )
        )

        original_dir = (
            session.session_directory
        )

        session_manager.save_session(
            session,
        )

        loaded = (
            session_manager.load_session(
                project_name,
            )
        )

        assert (
            loaded.session_directory
            == original_dir
        )


















class TestDeterministicBehavior:
    def test_list_sessions_is_repeatable(
        self,
        session_manager,
    ) -> None:
        session_manager.create_session(
            "project-a",
        )

        session_manager.create_session(
            "project-b",
        )

        first = (
            session_manager.list_sessions()
        )

        second = (
            session_manager.list_sessions()
        )

        first_names = [
            item.project_name
            for item in first
        ]

        second_names = [
            item.project_name
            for item in second
        ]

        assert (
            first_names
            == second_names
        )

    def test_session_stats_are_stable(
        self,
        session_manager,
        existing_session,
    ) -> None:
        first = (
            session_manager.get_session_stats(
                existing_session,
            )
        )

        second = (
            session_manager.get_session_stats(
                existing_session,
            )
        )

        assert first == second

    def test_multiple_loads_return_same_metadata(
        self,
        session_manager,
        project_name,
    ) -> None:
        session_manager.create_session(
            project_name,
        )

        first = (
            session_manager.load_session(
                project_name,
            )
        )

        second = (
            session_manager.load_session(
                project_name,
            )
        )

        assert (
            first.metadata.project_name
            == second.metadata.project_name
        )

        assert (
            first.metadata.created_at
            == second.metadata.created_at
        )

    def test_summary_is_repeatable(
        self,
        service,
    ) -> None:
        result = MagicMock()

        summary = {
            "project_name": "demo",
            "fact_count": 3,
            "evidence_count": 5,
        }

        result.to_summary.return_value = (
            summary
        )

        first = service.summarize(
            result,
        )

        second = service.summarize(
            result,
        )

        assert first == second

    def test_formatter_markdown_is_deterministic(
        self,
    ) -> None:
        from cortexfeed.investigation.prompts.composer import (
            PromptPackage,
        )

        from cortexfeed.investigation.prompts.formatter import (
            PromptFormatter,
        )

        formatter = (
            PromptFormatter()
        )

        package = PromptPackage(
            template_name="debugging",
            system_instructions="test",
            sections={
                "facts": [
                    "fact-a",
                    "fact-b",
                ],
            },
        )

        first = formatter.to_markdown(
            package,
        )

        second = formatter.to_markdown(
            package,
        )

        assert first == second

    def test_formatter_text_is_deterministic(
        self,
    ) -> None:
        from cortexfeed.investigation.prompts.composer import (
            PromptPackage,
        )

        from cortexfeed.investigation.prompts.formatter import (
            PromptFormatter,
        )

        formatter = (
            PromptFormatter()
        )

        package = PromptPackage(
            template_name="debugging",
            system_instructions="system",
            sections={
                "facts": [
                    "404 route",
                ],
            },
        )

        first = formatter.to_text(
            package,
        )

        second = formatter.to_text(
            package,
        )

        assert first == second

    def test_formatter_claude_is_deterministic(
        self,
    ) -> None:
        from cortexfeed.investigation.prompts.composer import (
            PromptPackage,
        )

        from cortexfeed.investigation.prompts.formatter import (
            PromptFormatter,
        )

        formatter = (
            PromptFormatter()
        )

        package = PromptPackage(
            template_name="debugging",
            system_instructions="system",
            sections={
                "facts": [
                    "404",
                ],
            },
        )

        first = formatter.to_claude(
            package,
        )

        second = formatter.to_claude(
            package,
        )

        assert first == second

    def test_formatter_gemini_is_deterministic(
        self,
    ) -> None:
        from cortexfeed.investigation.prompts.composer import (
            PromptPackage,
        )

        from cortexfeed.investigation.prompts.formatter import (
            PromptFormatter,
        )

        formatter = (
            PromptFormatter()
        )

        package = PromptPackage(
            template_name="debugging",
            system_instructions="system",
            sections={
                "facts": [
                    "route missing",
                ],
            },
        )

        assert (
            formatter.to_gemini(
                package,
            )
            == formatter.to_gemini(
                package,
            )
        )

    def test_formatter_chatgpt_is_deterministic(
        self,
    ) -> None:
        from cortexfeed.investigation.prompts.composer import (
            PromptPackage,
        )

        from cortexfeed.investigation.prompts.formatter import (
            PromptFormatter,
        )

        formatter = (
            PromptFormatter()
        )

        package = PromptPackage(
            template_name="debugging",
            system_instructions="system",
            sections={
                "facts": [
                    "api issue",
                ],
            },
        )

        assert (
            formatter.to_chatgpt(
                package,
            )
            == formatter.to_chatgpt(
                package,
            )
        )

    def test_formatter_local_is_deterministic(
        self,
    ) -> None:
        from cortexfeed.investigation.prompts.composer import (
            PromptPackage,
        )

        from cortexfeed.investigation.prompts.formatter import (
            PromptFormatter,
        )

        formatter = (
            PromptFormatter()
        )

        package = PromptPackage(
            template_name="debugging",
            system_instructions="system",
            sections={
                "facts": [
                    "backend failure",
                ],
            },
        )

        assert (
            formatter.to_local(
                package,
            )
            == formatter.to_local(
                package,
            )
        )

    def test_formatter_dispatch_is_stable(
        self,
    ) -> None:
        from cortexfeed.investigation.prompts.composer import (
            PromptPackage,
        )

        from cortexfeed.investigation.prompts.formatter import (
            PromptFormatter,
        )

        formatter = (
            PromptFormatter()
        )

        package = PromptPackage(
            template_name="debugging",
            system_instructions="system",
            sections={},
        )

        first = formatter.format(
            package,
            target="markdown",
        )

        second = formatter.format(
            package,
            target="markdown",
        )

        assert first == second