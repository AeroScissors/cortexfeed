# File: cortexfeed/knowledge/projects/registry.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = (
    Path("data")
    / "projects"
    / "registry.json"
)


@dataclass(slots=True)
class ProjectRecord:
    project_name: str
    project_path: str
    artifact_path: str
    indexed_at: str
    metadata_path: str


class ProjectRegistry:
    """
    Persistent registry of indexed projects.

    Tracks:

    - known projects
    - artifact locations
    - metadata locations
    - indexing timestamps

    Storage:

    data/projects/registry.json
    """

    def __init__(
        self,
        registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    ) -> None:
        self.registry_path = Path(registry_path)

        self.registry_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.registry_path.exists():
            self._save({"projects": []})

    def register(
        self,
        *,
        project_name: str,
        project_path: str,
        artifact_path: str,
        metadata_path: str,
    ) -> ProjectRecord:
        registry = self._load()

        record = ProjectRecord(
            project_name=project_name,
            project_path=project_path,
            artifact_path=artifact_path,
            metadata_path=metadata_path,
            indexed_at=datetime.now(
                timezone.utc
            ).isoformat(),
        )

        projects = registry["projects"]

        projects = [
            project
            for project in projects
            if project["project_path"] != project_path
        ]

        projects.append(asdict(record))

        projects.sort(
            key=lambda item: item[
                "project_name"
            ].lower()
        )

        registry["projects"] = projects

        self._save(registry)

        return record

    def get(
        self,
        project_name: str,
    ) -> ProjectRecord | None:
        registry = self._load()

        for project in registry["projects"]:
            if (
                project["project_name"].lower()
                == project_name.lower()
            ):
                return ProjectRecord(**project)

        return None

    def get_by_path(
        self,
        project_path: str,
    ) -> ProjectRecord | None:
        registry = self._load()

        normalized = str(
            Path(project_path).resolve()
        )

        for project in registry["projects"]:
            existing = str(
                Path(
                    project["project_path"]
                ).resolve()
            )

            if existing == normalized:
                return ProjectRecord(**project)

        return None

    def exists(
        self,
        project_name: str,
    ) -> bool:
        return self.get(project_name) is not None

    def remove(
        self,
        project_name: str,
    ) -> bool:
        registry = self._load()

        before = len(registry["projects"])

        registry["projects"] = [
            project
            for project in registry["projects"]
            if project["project_name"].lower()
            != project_name.lower()
        ]

        after = len(registry["projects"])

        self._save(registry)

        return before != after

    def list_projects(
        self,
    ) -> list[ProjectRecord]:
        registry = self._load()

        records = [
            ProjectRecord(**item)
            for item in registry["projects"]
        ]

        records.sort(
            key=lambda item: item.project_name.lower()
        )

        return records

    def count(self) -> int:
        return len(
            self._load()["projects"]
        )

    def _load(self) -> dict[str, Any]:
        with self.registry_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            return json.load(handle)

    def _save(
        self,
        payload: dict[str, Any],
    ) -> None:
        with self.registry_path.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                ensure_ascii=False,
            )


def register_project(
    *,
    project_name: str,
    project_path: str,
    artifact_path: str,
    metadata_path: str,
) -> ProjectRecord:
    registry = ProjectRegistry()

    return registry.register(
        project_name=project_name,
        project_path=project_path,
        artifact_path=artifact_path,
        metadata_path=metadata_path,
    )


def get_project(
    project_name: str,
) -> ProjectRecord | None:
    registry = ProjectRegistry()

    return registry.get(project_name)


def list_projects() -> list[ProjectRecord]:
    registry = ProjectRegistry()

    return registry.list_projects()