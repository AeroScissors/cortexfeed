# File: cortexfeed/knowledge/projects/manager.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.projects.loader import (
    ProjectLoader,
)
from cortexfeed.knowledge.projects.registry import (
    ProjectRegistry,
)


@dataclass(slots=True)
class ProjectContext:
    project_name: str
    project_path: str
    artifact_path: str
    tree: dict[str, Any]
    symbols: dict[str, Any]
    graph: dict[str, Any]
    metadata: dict[str, Any]


class ProjectManager:
    """
    Central project intelligence coordinator.

    Responsibilities:

    - Open projects
    - Build intelligence artifacts
    - Register projects
    - Load existing artifacts
    - Rebuild artifacts when requested
    - Provide project context to Investigation

    Entry point for CortexFeed V3.
    """

    def __init__(
        self,
        projects_root: str | Path = "data/projects",
    ) -> None:
        self.projects_root = Path(projects_root)
        self.registry = ProjectRegistry()

    def open_project(
        self,
        project_path: str | Path,
        *,
        rebuild: bool = False,
    ) -> ProjectContext:
        project_root = Path(project_path).resolve()

        if not project_root.exists():
            raise FileNotFoundError(
                f"Project not found: {project_root}"
            )

        project_name = project_root.name

        existing = self.registry.get_by_path(
            str(project_root)
        )

        if rebuild or existing is None:
            return self._build_project(
                project_root
            )

        artifact_path = Path(
            existing.artifact_path
        )

        if not self._artifacts_exist(
            artifact_path
        ):
            return self._build_project(
                project_root
            )

        return self._load_context(
            project_name=existing.project_name,
            project_path=existing.project_path,
            artifact_path=artifact_path,
        )

    def rebuild_project(
        self,
        project_path: str | Path,
    ) -> ProjectContext:
        return self.open_project(
            project_path,
            rebuild=True,
        )

    def load_project(
        self,
        project_name: str,
    ) -> ProjectContext:
        record = self.registry.get(
            project_name
        )

        if record is None:
            raise ValueError(
                f"Unknown project: {project_name}"
            )

        return self._load_context(
            project_name=record.project_name,
            project_path=record.project_path,
            artifact_path=Path(
                record.artifact_path
            ),
        )

    def list_projects(
        self,
    ) -> list[str]:
        return [
            project.project_name
            for project in self.registry.list_projects()
        ]

    def _build_project(
        self,
        project_root: Path,
    ) -> ProjectContext:
        loader = ProjectLoader(
            project_root=project_root,
            output_root=self.projects_root,
        )

        result = loader.load()

        artifact_path = (
            self.projects_root
            / project_root.name
        )

        metadata_path = (
            artifact_path
            / "metadata.json"
        )

        self.registry.register(
            project_name=project_root.name,
            project_path=str(project_root),
            artifact_path=str(
                artifact_path.resolve()
            ),
            metadata_path=str(
                metadata_path.resolve()
            ),
        )

        return ProjectContext(
            project_name=result["project"],
            project_path=str(project_root),
            artifact_path=str(
                artifact_path
            ),
            tree=result["tree"],
            symbols=result["symbols"],
            graph=result["graph"],
            metadata=result["metadata"],
        )

    def _load_context(
        self,
        *,
        project_name: str,
        project_path: str,
        artifact_path: Path,
    ) -> ProjectContext:
        tree = self._read_json(
            artifact_path / "tree.json"
        )

        symbols = self._read_json(
            artifact_path / "symbols.json"
        )

        graph = self._read_json(
            artifact_path / "graph.json"
        )

        metadata = self._read_json(
            artifact_path / "metadata.json"
        )

        return ProjectContext(
            project_name=project_name,
            project_path=project_path,
            artifact_path=str(
                artifact_path
            ),
            tree=tree,
            symbols=symbols,
            graph=graph,
            metadata=metadata,
        )

    @staticmethod
    def _artifacts_exist(
        artifact_path: Path,
    ) -> bool:
        required_files = (
            artifact_path / "tree.json",
            artifact_path / "symbols.json",
            artifact_path / "graph.json",
            artifact_path / "metadata.json",
        )

        return all(
            file.exists()
            for file in required_files
        )

    @staticmethod
    def _read_json(
        file_path: Path,
    ) -> dict[str, Any]:
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            return json.load(handle)


def open_project(
    project_path: str | Path,
    *,
    rebuild: bool = False,
) -> ProjectContext:
    manager = ProjectManager()

    return manager.open_project(
        project_path,
        rebuild=rebuild,
    )


def load_project(
    project_name: str,
) -> ProjectContext:
    manager = ProjectManager()

    return manager.load_project(
        project_name
    )