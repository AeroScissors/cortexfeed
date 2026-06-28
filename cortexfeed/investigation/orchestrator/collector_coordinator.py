# File: cortexfeed/investigation/orchestrator/collector_coordinator.py

from __future__ import annotations

from pathlib import Path

from cortexfeed.investigation.collector.file_collector import (
    FileCollector,
)
from cortexfeed.investigation.collector.log_collector import (
    LogCollector,
)
from cortexfeed.investigation.collector.models import (
    Evidence,
)
from cortexfeed.investigation.collector.project_collector import (
    ProjectCollector,
)
from cortexfeed.investigation.collector.terminal_collector import (
    TerminalCollector,
)
from cortexfeed.investigation.planner.models import (
    EvidencePlan,
    EvidenceType,
)

from .exceptions import (
    CollectorConfigurationError,
    UnsupportedEvidenceTypeError,
)


class CollectorCoordinator:
    def __init__(
        self,
        *,
        project_root: str | Path | None = None,
        file_paths: dict[EvidenceType, str | Path] | None = None,
        terminal_command: str | None = None,
        terminal_stdout: str = "",
        terminal_stderr: str = "",
        terminal_exit_code: int = 0,
    ) -> None:
        self.project_root = (
            Path(project_root)
            if project_root is not None
            else None
        )
        self.file_paths = file_paths or {}
        self.terminal_command = terminal_command
        self.terminal_stdout = terminal_stdout
        self.terminal_stderr = terminal_stderr
        self.terminal_exit_code = terminal_exit_code

    def collect(self, plan: EvidencePlan) -> list[Evidence]:
        collected: list[Evidence] = []
        for requirement in plan.collection_order:
            collector_evidence = self._collect_for_type(requirement.evidence_type)
            collected.extend(collector_evidence)
        return collected

    def _collect_for_type(self, evidence_type: EvidenceType) -> list[Evidence]:
        if evidence_type == EvidenceType.PROJECT_STRUCTURE:
            return self._collect_project_structure()

        if evidence_type in (
            EvidenceType.REPOSITORY_CODE,
            EvidenceType.API_ROUTES,
            EvidenceType.CONFIG_FILE,
            EvidenceType.DATABASE_SCHEMA,
        ):
            return self._collect_file_evidence(evidence_type)

        if evidence_type in (
            EvidenceType.SERVER_LOGS,
            EvidenceType.STACK_TRACE,
        ):
            return self._collect_log_evidence(evidence_type)

        if evidence_type in (
            EvidenceType.TERMINAL_OUTPUT,
            EvidenceType.TEST_RESULTS,
        ):
            return self._collect_terminal_evidence()

        if evidence_type == EvidenceType.NETWORK_TRACE:
            # No live network collector — treat like file evidence.
            # If a file path was supplied use it, otherwise skip silently.
            return self._collect_log_evidence(evidence_type)

        # Unknown type — skip silently instead of crashing so a single
        # missing collector doesn't abort the entire investigation.
        return []

    def _collect_project_structure(self) -> list[Evidence]:
        if self.project_root is None:
            return []
        collector = ProjectCollector(self.project_root)
        return collector.collect()

    def _collect_file_evidence(self, evidence_type: EvidenceType) -> list[Evidence]:
        path = self.file_paths.get(evidence_type)
        if path is None:
            return []
        collector = FileCollector(path)
        return collector.collect()

    def _collect_log_evidence(self, evidence_type: EvidenceType) -> list[Evidence]:
        path = self.file_paths.get(evidence_type)
        if path is None:
            return []
        collector = LogCollector(path)
        return collector.collect()

    def _collect_terminal_evidence(self) -> list[Evidence]:
        if not self.terminal_command:
            return []
        collector = TerminalCollector(
            command=self.terminal_command,
            stdout=self.terminal_stdout,
            stderr=self.terminal_stderr,
            exit_code=self.terminal_exit_code,
        )
        return collector.collect()