# File: cortexfeed/tests/investigation/test_investigation_v2.py
"""
Real-execution investigation suite for CortexFeed V2.

Distinct from test_investigation.py (mock-driven, 68 tests).
This suite maximises real subsystem execution.

Allowed to fail when it discovers genuine integration defects.
Do not weaken assertions to force green.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Planner imports
# ---------------------------------------------------------------------------
from cortexfeed.investigation.planner.intent_analyzer import (
    RuleBasedIntentClassifier,
)
from cortexfeed.investigation.planner.evidence_planner import (
    EvidencePlanner,
)
from cortexfeed.investigation.planner.question_generator import (
    TemplateQuestionStrategy,
)
from cortexfeed.investigation.planner.models import (
    EvidenceType as PlannerEvidenceType,
    InvestigationDomain,
    InvestigationType,
)

# ---------------------------------------------------------------------------
# Collector imports
# ---------------------------------------------------------------------------
from cortexfeed.investigation.collector.file_collector import (
    FileCollector,
)
from cortexfeed.investigation.collector.log_collector import (
    LogCollector,
)
from cortexfeed.investigation.collector.terminal_collector import (
    TerminalCollector,
)
from cortexfeed.investigation.collector.project_collector import (
    ProjectCollector,
)
from cortexfeed.investigation.collector.models import (
    EvidenceType as CollectorEvidenceType,
)

# ---------------------------------------------------------------------------
# Analyst imports
# ---------------------------------------------------------------------------
from cortexfeed.investigation.analyst.fact_extractor import (
    Evidence as AnalystEvidence,
    FactExtractor,
)
from cortexfeed.investigation.analyst.hypothesis_engine import (
    Fact as AnalystFact,
    HypothesisEngine,
    HypothesisStatus,
)

# ---------------------------------------------------------------------------
# Prompt imports
# ---------------------------------------------------------------------------
from cortexfeed.investigation.prompts.composer import PromptComposer

# ---------------------------------------------------------------------------
# Session / persistence imports
# ---------------------------------------------------------------------------
from cortexfeed.investigation.sessions.manager import SessionManager
from cortexfeed.investigation.sessions.facts import FactRegistry
from cortexfeed.investigation.sessions.hypotheses import HypothesisRegistry
from cortexfeed.investigation.sessions.evidence import EvidenceRegistry
from cortexfeed.investigation.sessions.timeline import TimelineStore

# ---------------------------------------------------------------------------
# Orchestrator imports
# ---------------------------------------------------------------------------
from cortexfeed.investigation.orchestrator.engine import (
    InvestigationEngine,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_analyst_evidence(content: str) -> AnalystEvidence:
    from datetime import datetime, timezone
    from uuid import uuid4
    return AnalystEvidence(
        id=str(uuid4()),
        source="test",
        content=content,
        created_at=datetime.now(timezone.utc),
    )


def _make_analyst_fact(statement: str) -> AnalystFact:
    from datetime import datetime, timezone
    from uuid import uuid4
    return AnalystFact(
        id=str(uuid4()),
        statement=statement,
        confidence=1.0,
        evidence_ids=[str(uuid4())],
        source="test",
        created_at=datetime.now(timezone.utc),
    )


# ===========================================================================
# TestRealPlannerExecution
# ===========================================================================

class TestRealPlannerExecution:

    def test_backend_debugging_plan(self):
        classifier = RuleBasedIntentClassifier()
        planner = EvidencePlanner()

        intent = classifier.classify("Debug missing API route on the backend server")

        assert intent.investigation_type == InvestigationType.DEBUGGING
        assert intent.domain == InvestigationDomain.BACKEND

        plan = planner.create_plan(intent)

        required_types = {r.evidence_type for r in plan.required}
        assert PlannerEvidenceType.SERVER_LOGS in required_types
        assert PlannerEvidenceType.API_ROUTES in required_types
        assert PlannerEvidenceType.REPOSITORY_CODE in required_types
        assert PlannerEvidenceType.STACK_TRACE in required_types

        # collection_order must be a sorted subset of missing
        assert len(plan.collection_order) == len(plan.missing)

    def test_auth_security_plan(self):
        classifier = RuleBasedIntentClassifier()
        planner = EvidencePlanner()

        intent = classifier.classify("Review JWT token auth security vulnerability")

        assert intent.investigation_type == InvestigationType.SECURITY
        assert intent.domain == InvestigationDomain.AUTH

        plan = planner.create_plan(intent)

        required_types = {r.evidence_type for r in plan.required}
        assert PlannerEvidenceType.CONFIG_FILE in required_types
        assert PlannerEvidenceType.API_ROUTES in required_types
        assert PlannerEvidenceType.REPOSITORY_CODE in required_types

    def test_question_generation(self):
        classifier = RuleBasedIntentClassifier()
        planner = EvidencePlanner()
        generator = TemplateQuestionStrategy()

        intent = classifier.classify("Debug missing API route on the backend server")
        plan = planner.create_plan(intent)
        bundle = generator.generate(plan)

        assert len(bundle.questions) == len(plan.collection_order)

        # Verify deterministic label mapping
        assert any("server logs" in q for q in bundle.questions)
        assert any("API routes" in q for q in bundle.questions)

        # All questions follow the template
        for question in bundle.questions:
            assert question.startswith("Please provide ")

        assert bundle.combined_prompt.startswith("Please provide:")


# ===========================================================================
# TestRealCollectors
# ===========================================================================

class TestRealCollectors:

    def test_file_collector_metadata(self, tmp_path):
        target = tmp_path / "routes.txt"
        target.write_text("GET /users\nPOST /users\nGET /promise\n", encoding="utf-8")

        collector = FileCollector(target)
        evidence_list = collector.collect()

        assert len(evidence_list) == 1
        ev = evidence_list[0]

        assert ev.evidence_type == CollectorEvidenceType.FILE
        assert ev.metadata["filename"] == "routes.txt"
        assert ev.metadata["extension"] == ".txt"
        assert isinstance(ev.metadata["size_bytes"], int)
        assert ev.metadata["size_bytes"] > 0
        assert len(ev.metadata["sha256"]) == 64   # hex sha256
        assert "GET /promise" in ev.content

    def test_file_collector_chunking(self, tmp_path):
        # Write a file with 10 lines; chunk at 3
        lines = [f"line {i}" for i in range(10)]
        target = tmp_path / "big.py"
        target.write_text("\n".join(lines), encoding="utf-8")

        collector = FileCollector(target, chunk_size_lines=3)
        chunks = collector.collect_chunks()

        assert len(chunks) == 4   # ceil(10/3)

        for chunk in chunks:
            assert hasattr(chunk, "chunk_index")
            assert hasattr(chunk, "total_chunks")
            assert chunk.total_chunks == 4
            assert hasattr(chunk, "start_line")
            assert hasattr(chunk, "end_line")
            assert chunk.start_line >= 1

        # Indices are contiguous
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(4))

    def test_log_collector_trim(self, tmp_path):
        # Write a log that exceeds max_lines
        log_lines = [f"[INFO] event {i}" for i in range(200)]
        log_file = tmp_path / "server.log"
        log_file.write_text("\n".join(log_lines), encoding="utf-8")

        collector = LogCollector(
            log_file,
            max_lines=50,
            head_lines=10,
            tail_lines=20,
        )
        evidence_list = collector.collect()
        ev = evidence_list[0]

        assert ev.evidence_type == CollectorEvidenceType.LOG
        assert ev.metadata["original_line_count"] == 200
        assert ev.metadata["was_trimmed"] is True
        assert ev.metadata["retained_line_count"] < 200
        assert "TRIMMED LOG" in ev.content

    def test_log_collector_no_trim(self, tmp_path):
        log_lines = [f"[INFO] event {i}" for i in range(20)]
        log_file = tmp_path / "small.log"
        log_file.write_text("\n".join(log_lines), encoding="utf-8")

        collector = LogCollector(log_file, max_lines=5000)
        evidence_list = collector.collect()
        ev = evidence_list[0]

        assert ev.metadata["was_trimmed"] is False
        assert ev.metadata["original_line_count"] == 20
        assert ev.metadata["retained_line_count"] == 20

    def test_terminal_collector_metadata(self):
        collector = TerminalCollector(
            command="pytest --tb=short",
            stdout="5 passed",
            stderr="",
            exit_code=0,
        )
        evidence_list = collector.collect()
        ev = evidence_list[0]

        assert ev.evidence_type == CollectorEvidenceType.TERMINAL
        assert ev.metadata["command"] == "pytest --tb=short"
        assert ev.metadata["exit_code"] == 0
        assert ev.metadata["stdout_length"] > 0
        assert ev.metadata["stderr_length"] == 0
        assert ev.metadata["has_errors"] is False
        assert "STDOUT" in ev.content
        assert "STDERR" in ev.content

    def test_terminal_collector_has_errors(self):
        collector = TerminalCollector(
            command="python app.py",
            stdout="",
            stderr="ImportError: No module named foo",
            exit_code=1,
        )
        evidence_list = collector.collect()
        ev = evidence_list[0]

        assert ev.metadata["has_errors"] is True
        assert ev.metadata["exit_code"] == 1

    def test_project_collector_summary(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "app.ts").write_text("const x = 1;", encoding="utf-8")
        (tmp_path / "README.md").write_text("# project", encoding="utf-8")

        collector = ProjectCollector(tmp_path)
        evidence_list = collector.collect()

        # First item must be PROJECT_SUMMARY
        summary_ev = evidence_list[0]
        assert summary_ev.evidence_type == CollectorEvidenceType.PROJECT_SUMMARY
        assert summary_ev.metadata["file_count"] >= 3
        assert "extensions" in summary_ev.metadata
        assert "languages" in summary_ev.metadata
        assert "Python" in summary_ev.metadata["languages"]

    def test_project_collector_file_discovery(self, tmp_path):
        (tmp_path / "routes.py").write_text("GET /users", encoding="utf-8")
        (tmp_path / "models.py").write_text("class User: pass", encoding="utf-8")
        (tmp_path / "README.md").write_text("# docs", encoding="utf-8")

        collector = ProjectCollector(tmp_path)
        relevant = collector.discover_relevant_files(["routes"])

        assert len(relevant) >= 1
        names = [p.name for p in relevant]
        assert "routes.py" in names


# ===========================================================================
# TestRealAnalysis
# ===========================================================================

class TestRealAnalysis:

    def test_fact_extraction_404(self):
        extractor = FactExtractor()
        ev = _make_analyst_evidence("GET /promise returns 404")
        facts = extractor.extract([ev])

        assert len(facts) == 1
        assert "GET /promise returns 404" in facts[0].statement
        assert facts[0].confidence == 1.0
        assert len(facts[0].evidence_ids) == 1

    def test_fact_extraction_deduplication(self):
        extractor = FactExtractor()
        content = "connection refused on port 5432"
        ev1 = _make_analyst_evidence(content)
        ev2 = _make_analyst_evidence(content)

        facts = extractor.extract([ev1, ev2])

        # Identical content -> same hash -> deduplicated
        assert len(facts) == 1

    def test_hypothesis_generation_404(self):
        engine = HypothesisEngine()
        fact = _make_analyst_fact("GET /promise returns 404")
        hypotheses = engine.generate([fact])

        statements = {h.statement for h in hypotheses}
        assert "Requested route is not registered" in statements
        assert "Request path is incorrect" in statements

    def test_hypothesis_generation_connection_refused(self):
        engine = HypothesisEngine()
        fact = _make_analyst_fact("connection refused connecting to Redis")
        hypotheses = engine.generate([fact])

        statements = {h.statement for h in hypotheses}
        assert "Target service is not running" in statements
        assert "Network configuration issue exists" in statements

    def test_hypothesis_generation_timeout(self):
        engine = HypothesisEngine()
        fact = _make_analyst_fact("request timeout after 30s")
        hypotheses = engine.generate([fact])

        statements = {h.statement for h in hypotheses}
        assert "Dependency is responding too slowly" in statements

    def test_hypothesis_deduplication(self):
        engine = HypothesisEngine()
        fact1 = _make_analyst_fact("GET /a returns 404")
        fact2 = _make_analyst_fact("GET /b returns 404")

        hypotheses = engine.generate([fact1, fact2])

        ids = [h.id for h in hypotheses]
        # IDs are deterministic by statement hash; same statement -> same id
        assert len(ids) == len(set(ids))

        # "Requested route is not registered" appears exactly once
        matching = [h for h in hypotheses if h.statement == "Requested route is not registered"]
        assert len(matching) == 1
        # But it has two supporting facts
        assert len(matching[0].supporting_facts) == 2

    def test_hypothesis_status_update(self):
        engine = HypothesisEngine()
        fact1 = _make_analyst_fact("GET /a returns 404")
        fact2 = _make_analyst_fact("GET /b returns 404")

        hypotheses = engine.generate([fact1, fact2])
        updated = engine.update_status(hypotheses)

        # "Requested route is not registered" has 2 supporting facts -> SUPPORTED
        route_hyp = next(
            h for h in updated
            if h.statement == "Requested route is not registered"
        )
        assert route_hyp.status == HypothesisStatus.SUPPORTED
        assert route_hyp.score >= 0.5


# ===========================================================================
# TestPromptGeneration
# ===========================================================================

class TestPromptGeneration:

    def test_prompt_package_creation(self):
        composer = PromptComposer()
        package = composer.compose(
            project="test-project",
            current_issue="GET /promise returns 404",
            facts=["GET /promise returns 404"],
            hypotheses=["Requested route is not registered"],
            evidence=["server.log"],
        )

        assert package.template_name is not None
        assert "verified_facts" in package.sections
        assert "active_hypotheses" in package.sections
        assert "relevant_evidence" in package.sections

        assert "GET /promise returns 404" in package.sections["verified_facts"]
        assert "Requested route is not registered" in package.sections["active_hypotheses"]
        assert "server.log" in package.sections["relevant_evidence"]

    def test_prompt_determinism(self):
        composer = PromptComposer()

        kwargs = dict(
            project="test-project",
            current_issue="debug route",
            facts=["fact A", "fact B"],
            hypotheses=["hypothesis X"],
            evidence=["routes.txt"],
        )

        p1 = composer.compose(**kwargs)
        p2 = composer.compose(**kwargs)

        assert p1.template_name == p2.template_name
        assert p1.system_instructions == p2.system_instructions
        assert p1.sections == p2.sections

    def test_prompt_none_lists_become_empty(self):
        composer = PromptComposer()
        package = composer.compose(
            project="p",
            current_issue="issue",
            facts=None,
            hypotheses=None,
            evidence=None,
        )

        assert package.sections["verified_facts"] == []
        assert package.sections["active_hypotheses"] == []
        assert package.sections["relevant_evidence"] == []


# ===========================================================================
# TestEngineEndToEnd
# ===========================================================================

class TestEngineEndToEnd:

    @pytest.fixture()
    def investigation_files(self, tmp_path):
        server_log = tmp_path / "server.log"
        server_log.write_text(
            textwrap.dedent("""\
                [INFO]  Server started on port 8000
                [ERROR] GET /promise returns 404
                [ERROR] Route not found: /promise
            """),
            encoding="utf-8",
        )

        routes_file = tmp_path / "routes.txt"
        routes_file.write_text(
            textwrap.dedent("""\
                GET /users
                POST /users
                GET /users/:id
            """),
            encoding="utf-8",
        )

        repository_file = tmp_path / "repository.py"
        repository_file.write_text(
            textwrap.dedent("""\
                from fastapi import APIRouter
                router = APIRouter()

                @router.get("/users")
                def list_users():
                    return []
            """),
            encoding="utf-8",
        )

        trace_file = tmp_path / "trace.log"
        trace_file.write_text(
            textwrap.dedent("""\
                Traceback (most recent call last):
                  File "app.py", line 42, in handle_request
                    raise HTTPException(status_code=404)
                fastapi.exceptions.HTTPException: 404
            """),
            encoding="utf-8",
        )

        return {
            "server_log": server_log,
            "routes_file": routes_file,
            "repository_file": repository_file,
            "trace_file": trace_file,
        }

    def test_end_to_end_investigation(self, tmp_path, investigation_files):
        sessions_root = tmp_path / "sessions"

        engine = InvestigationEngine(
            sessions_root=sessions_root,
            file_paths={
                PlannerEvidenceType.SERVER_LOGS: investigation_files["server_log"],
                PlannerEvidenceType.API_ROUTES: investigation_files["routes_file"],
                PlannerEvidenceType.REPOSITORY_CODE: investigation_files["repository_file"],
                PlannerEvidenceType.STACK_TRACE: investigation_files["trace_file"],
            },
        )

        result = engine.investigate(
            request="Debug missing endpoint on the backend server",
            project_name="test-project",
        )

        assert result.evidence_count > 0
        assert result.fact_count > 0
        assert result.hypothesis_count > 0

    def test_end_to_end_hypothesis_content(self, tmp_path, investigation_files):
        sessions_root = tmp_path / "sessions"

        engine = InvestigationEngine(
            sessions_root=sessions_root,
            file_paths={
                PlannerEvidenceType.SERVER_LOGS: investigation_files["server_log"],
                PlannerEvidenceType.API_ROUTES: investigation_files["routes_file"],
                PlannerEvidenceType.REPOSITORY_CODE: investigation_files["repository_file"],
                PlannerEvidenceType.STACK_TRACE: investigation_files["trace_file"],
            },
        )

        result = engine.investigate(
            request="Debug missing endpoint on the backend server",
            project_name="test-project",
        )

        session = result.session
        hypothesis_statements = {h.statement for h in session.hypotheses.list()}

        assert "Requested route is not registered" in hypothesis_statements

    def test_end_to_end_prompt_sections_populated(self, tmp_path, investigation_files):
        sessions_root = tmp_path / "sessions"

        engine = InvestigationEngine(
            sessions_root=sessions_root,
            file_paths={
                PlannerEvidenceType.SERVER_LOGS: investigation_files["server_log"],
                PlannerEvidenceType.API_ROUTES: investigation_files["routes_file"],
                PlannerEvidenceType.REPOSITORY_CODE: investigation_files["repository_file"],
                PlannerEvidenceType.STACK_TRACE: investigation_files["trace_file"],
            },
        )

        result = engine.investigate(
            request="Debug missing endpoint on the backend server",
            project_name="test-project",
        )

        pkg = result.prompt_package
        assert len(pkg.sections["verified_facts"]) > 0
        assert len(pkg.sections["active_hypotheses"]) > 0
        assert len(pkg.sections["relevant_evidence"]) > 0

    def test_end_to_end_result_summary(self, tmp_path, investigation_files):
        sessions_root = tmp_path / "sessions"

        engine = InvestigationEngine(
            sessions_root=sessions_root,
            file_paths={
                PlannerEvidenceType.SERVER_LOGS: investigation_files["server_log"],
                PlannerEvidenceType.API_ROUTES: investigation_files["routes_file"],
                PlannerEvidenceType.REPOSITORY_CODE: investigation_files["repository_file"],
                PlannerEvidenceType.STACK_TRACE: investigation_files["trace_file"],
            },
        )

        result = engine.investigate(
            request="Debug missing endpoint on the backend server",
            project_name="test-project",
        )

        summary = result.to_summary()
        assert summary["project_name"] == "test-project"
        assert summary["intent"] == InvestigationType.DEBUGGING.value
        assert summary["domain"] == InvestigationDomain.BACKEND.value
        assert summary["evidence_count"] > 0
        assert summary["fact_count"] > 0
        assert summary["hypothesis_count"] > 0


# ===========================================================================
# TestPersistenceEndToEnd
# ===========================================================================

class TestPersistenceEndToEnd:

    @pytest.fixture()
    def persisted_session(self, tmp_path):
        """Run an investigation, return (sessions_root, project_name)."""
        server_log = tmp_path / "server.log"
        server_log.write_text(
            "[ERROR] GET /promise returns 404\n[ERROR] connection refused\n",
            encoding="utf-8",
        )
        routes_file = tmp_path / "routes.txt"
        routes_file.write_text("GET /users\n", encoding="utf-8")
        repo_file = tmp_path / "repo.py"
        repo_file.write_text("# backend code\n", encoding="utf-8")
        trace_file = tmp_path / "trace.log"
        trace_file.write_text("HTTPException: 404\n", encoding="utf-8")

        sessions_root = tmp_path / "sessions"

        engine = InvestigationEngine(
            sessions_root=sessions_root,
            file_paths={
                PlannerEvidenceType.SERVER_LOGS: server_log,
                PlannerEvidenceType.API_ROUTES: routes_file,
                PlannerEvidenceType.REPOSITORY_CODE: repo_file,
                PlannerEvidenceType.STACK_TRACE: trace_file,
            },
        )

        engine.investigate(
            request="Debug missing endpoint on the backend server",
            project_name="persist-test",
        )

        return sessions_root, "persist-test"

    def test_facts_survive_reload(self, persisted_session):
        sessions_root, project_name = persisted_session
        manager = SessionManager(sessions_root)
        session = manager.load_session(project_name)

        assert session.facts.count > 0

    def test_hypotheses_survive_reload(self, persisted_session):
        sessions_root, project_name = persisted_session
        manager = SessionManager(sessions_root)
        session = manager.load_session(project_name)

        assert len(session.hypotheses.list()) > 0

    def test_evidence_survives_reload(self, persisted_session):
        sessions_root, project_name = persisted_session
        manager = SessionManager(sessions_root)
        session = manager.load_session(project_name)

        assert len(session.evidence.list()) > 0

    def test_timeline_survives_reload(self, persisted_session):
        sessions_root, project_name = persisted_session
        manager = SessionManager(sessions_root)
        session = manager.load_session(project_name)

        events = session.timeline.list_events()
        assert len(events) > 0

    def test_persistence_files_exist(self, persisted_session):
        sessions_root, project_name = persisted_session
        session_dir = sessions_root / project_name

        assert (session_dir / "session.json").exists()
        assert (session_dir / "facts.json").exists()
        assert (session_dir / "hypotheses.json").exists()
        assert (session_dir / "evidence.json").exists()
        assert (session_dir / "timeline.jsonl").exists()
        assert (session_dir / "memory.json").exists()

    def test_hypothesis_content_survives_reload(self, persisted_session):
        sessions_root, project_name = persisted_session
        manager = SessionManager(sessions_root)
        session = manager.load_session(project_name)

        statements = {h.statement for h in session.hypotheses.list()}
        assert "Requested route is not registered" in statements

    def test_second_investigation_appends_not_duplicates(self, tmp_path):
        server_log = tmp_path / "server.log"
        server_log.write_text("[ERROR] GET /promise returns 404\n", encoding="utf-8")
        routes_file = tmp_path / "routes.txt"
        routes_file.write_text("GET /users\n", encoding="utf-8")
        repo_file = tmp_path / "repo.py"
        repo_file.write_text("# code\n", encoding="utf-8")
        trace_file = tmp_path / "trace.log"
        trace_file.write_text("404\n", encoding="utf-8")

        sessions_root = tmp_path / "sessions"
        file_paths = {
            PlannerEvidenceType.SERVER_LOGS: server_log,
            PlannerEvidenceType.API_ROUTES: routes_file,
            PlannerEvidenceType.REPOSITORY_CODE: repo_file,
            PlannerEvidenceType.STACK_TRACE: trace_file,
        }

        engine1 = InvestigationEngine(sessions_root=sessions_root, file_paths=file_paths)
        r1 = engine1.investigate(request="Debug broken backend server", project_name="append-test")

        engine2 = InvestigationEngine(sessions_root=sessions_root, file_paths=file_paths)
        r2 = engine2.investigate(request="Debug broken backend server again", project_name="append-test")

        # Session is resumed; hypothesis deduplication must not create duplicates
        statements = [h.statement for h in r2.session.hypotheses.list()]
        assert len(statements) == len(set(statements))