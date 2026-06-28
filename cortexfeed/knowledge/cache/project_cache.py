# File: cortexfeed/knowledge/cache/project_cache.py

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CACHE_SCHEMA_VERSION = "1.0"


@dataclass(slots=True)
class CachedProject:
    project_name: str
    project_path: str
    artifact_path: str
    last_indexed: str
    repository_hash: str
    file_count: int


class ProjectCache:
    """
    Project Intelligence cache layer.

    Responsibilities:

    - cache metadata
    - repository hash tracking
    - change detection
    - cache invalidation
    - incremental indexing support

    Storage:

    data/cache/projects/<project>.json
    """

    def __init__(
        self,
        cache_root: str | Path = "data/cache/projects",
    ) -> None:
        self.cache_root = Path(cache_root)

        self.cache_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def get(
        self,
        project_name: str,
    ) -> CachedProject | None:
        cache_file = (
            self.cache_root
            / f"{project_name}.json"
        )

        if not cache_file.exists():
            return None

        with cache_file.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        return CachedProject(
            **payload["project"]
        )

    def save(
        self,
        *,
        project_name: str,
        project_path: str,
        artifact_path: str,
    ) -> CachedProject:
        project_root = Path(
            project_path
        ).resolve()

        repository_hash = (
            self.compute_repository_hash(
                project_root
            )
        )

        file_count = len(
            self._tracked_files(
                project_root
            )
        )

        project = CachedProject(
            project_name=project_name,
            project_path=str(project_root),
            artifact_path=artifact_path,
            last_indexed=datetime.now(
                timezone.utc
            ).isoformat(),
            repository_hash=repository_hash,
            file_count=file_count,
        )

        payload = {
            "schema_version": (
                CACHE_SCHEMA_VERSION
            ),
            "project": asdict(project),
        }

        cache_file = (
            self.cache_root
            / f"{project_name}.json"
        )

        with cache_file.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                ensure_ascii=False,
            )

        return project

    def delete(
        self,
        project_name: str,
    ) -> bool:
        cache_file = (
            self.cache_root
            / f"{project_name}.json"
        )

        if not cache_file.exists():
            return False

        cache_file.unlink()

        return True

    def invalidate(
        self,
        project_name: str,
    ) -> bool:
        return self.delete(
            project_name
        )

    def requires_reindex(
        self,
        project_name: str,
        project_root: str | Path,
    ) -> bool:
        cached = self.get(
            project_name
        )

        if cached is None:
            return True

        current_hash = (
            self.compute_repository_hash(
                project_root
            )
        )

        return (
            current_hash
            != cached.repository_hash
        )

    def compute_repository_hash(
        self,
        project_root: str | Path,
    ) -> str:
        project_root = Path(
            project_root
        ).resolve()

        hasher = hashlib.sha256()

        for file_path in self._tracked_files(
            project_root
        ):
            relative = (
                file_path.relative_to(
                    project_root
                )
                .as_posix()
            )

            hasher.update(
                relative.encode("utf-8")
            )

            try:
                stat = file_path.stat()

                hasher.update(
                    str(
                        stat.st_size
                    ).encode("utf-8")
                )

                hasher.update(
                    str(
                        stat.st_mtime_ns
                    ).encode("utf-8")
                )
            except OSError:
                continue

        return hasher.hexdigest()

    def list_cached_projects(
        self,
    ) -> list[CachedProject]:
        projects: list[
            CachedProject
        ] = []

        for cache_file in sorted(
            self.cache_root.glob(
                "*.json"
            )
        ):
            try:
                with cache_file.open(
                    "r",
                    encoding="utf-8",
                ) as handle:
                    payload = json.load(
                        handle
                    )

                projects.append(
                    CachedProject(
                        **payload[
                            "project"
                        ]
                    )
                )

            except (
                OSError,
                json.JSONDecodeError,
                KeyError,
            ):
                continue

        return projects

    def _tracked_files(
        self,
        project_root: Path,
    ) -> list[Path]:
        ignored = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            "build",
            "dist",
        }

        files: list[Path] = []

        for path in project_root.rglob("*"):
            if not path.is_file():
                continue

            if any(
                part in ignored
                for part in path.parts
            ):
                continue

            files.append(path)

        files.sort(
            key=lambda item: str(
                item
            ).lower()
        )

        return files


def get_project_cache(
    project_name: str,
) -> CachedProject | None:
    cache = ProjectCache()

    return cache.get(project_name)


def project_requires_reindex(
    *,
    project_name: str,
    project_root: str | Path,
) -> bool:
    cache = ProjectCache()

    return cache.requires_reindex(
        project_name=project_name,
        project_root=project_root,
    )