# File: cortexfeed/knowledge/indexing/project_tree.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        ".github",
        ".idea",
        ".vscode",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "build",
        "dist",
        "target",
        ".dart_tool",
        ".next",
        ".turbo",
        ".gradle",
        "coverage",
    }
)

IGNORED_FILES: frozenset[str] = frozenset(
    {
        ".DS_Store",
        "Thumbs.db",
    }
)


@dataclass(slots=True)
class TreeNode:
    """
    Deterministic representation of a repository node.
    """

    name: str
    path: str
    node_type: str
    children: list["TreeNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProjectTreeBuilder:
    """
    Builds a deterministic repository tree.

    Output is stable across runs by:
    - sorting directories alphabetically
    - sorting files alphabetically
    - normalizing paths
    """

    def __init__(self, project_root: str | Path) -> None:
        self._root = Path(project_root).resolve()

        if not self._root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {self._root}"
            )

        if not self._root.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {self._root}"
            )

    @property
    def project_root(self) -> Path:
        return self._root

    def build(self) -> TreeNode:
        return self._build_directory(self._root)

    def export(self) -> dict[str, Any]:
        return self.build().to_dict()

    def save(self, output_path: str | Path) -> Path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open(
            mode="w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                self.export(),
                handle,
                indent=2,
                ensure_ascii=False,
                sort_keys=False,
            )

        return output_file

    def _build_directory(self, directory: Path) -> TreeNode:
        relative_path = self._relative_path(directory)

        node = TreeNode(
            name=directory.name,
            path=relative_path,
            node_type="directory",
        )

        directories: list[Path] = []
        files: list[Path] = []

        for child in directory.iterdir():
            if self._should_ignore(child):
                continue

            if child.is_dir():
                directories.append(child)
            else:
                files.append(child)

        directories.sort(key=lambda item: item.name.lower())
        files.sort(key=lambda item: item.name.lower())

        for child_directory in directories:
            node.children.append(
                self._build_directory(child_directory)
            )

        for child_file in files:
            node.children.append(
                TreeNode(
                    name=child_file.name,
                    path=self._relative_path(child_file),
                    node_type="file",
                )
            )

        return node

    def _should_ignore(self, path: Path) -> bool:
        if path.name in IGNORED_FILES:
            return True

        if path.is_dir() and path.name in IGNORED_DIRECTORIES:
            return True

        return False

    def _relative_path(self, path: Path) -> str:
        if path == self._root:
            return "."

        return path.relative_to(self._root).as_posix()


def build_project_tree(
    project_root: str | Path,
) -> dict[str, Any]:
    """
    Convenience API used by higher-level services.
    """

    builder = ProjectTreeBuilder(project_root)
    return builder.export()


def save_project_tree(
    project_root: str | Path,
    output_path: str | Path,
) -> Path:
    """
    Build and persist tree.json.
    """

    builder = ProjectTreeBuilder(project_root)
    return builder.save(output_path)