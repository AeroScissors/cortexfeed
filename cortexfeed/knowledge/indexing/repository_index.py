# File: cortexfeed/knowledge/indexing/repository_index.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.graph.graph_builder import (
    build_graph,
)
from cortexfeed.knowledge.graph.graph_storage import (
    GraphStorage,
)
from cortexfeed.knowledge.indexing.project_tree import (
    build_project_tree,
)
from cortexfeed.knowledge.indexing.symbol_index import (
    build_symbol_index,
)
from cortexfeed.knowledge.resolver.dependency_resolver import (
    resolve_dependencies,
)


@dataclass(slots=True)
class RepositoryArtifacts:
    project_name: str
    project_path: str
    tree: dict[str, Any]
    symbols: dict[str, Any]
    dependencies: dict[str, Any]
    graph: dict[str, Any]


class RepositoryIndexer:
    """
    Top-level repository intelligence orchestrator.

    Pipeline:

        RepositoryIndexer
                ↓
        ProjectTreeBuilder
                ↓
        SymbolIndexer
                ↓
        DependencyResolver
                ↓
        GraphBuilder
                ↓
        GraphStorage

    Produces all intelligence artifacts required by
    CortexFeed Project Intelligence.
    """

    def __init__(
        self,
        project_root: str | Path,
    ) -> None:
        self.project_root = Path(project_root).resolve()

        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project root not found: {self.project_root}"
            )

        if not self.project_root.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {self.project_root}"
            )

    @property
    def project_name(self) -> str:
        return self.project_root.name

    def build(
        self,
    ) -> RepositoryArtifacts:
        tree = build_project_tree(
            self.project_root
        )

        symbols = build_symbol_index(
            self.project_root
        )

        dependencies = resolve_dependencies(
            self.project_root
        )

        graph = build_graph(
            self.project_root
        )

        return RepositoryArtifacts(
            project_name=self.project_name,
            project_path=str(self.project_root),
            tree=tree,
            symbols=symbols,
            dependencies=dependencies,
            graph=graph,
        )

    def persist(
        self,
        output_directory: str | Path,
    ) -> RepositoryArtifacts:
        artifacts = self.build()

        output_directory = Path(
            output_directory
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._write_json(
            output_directory / "tree.json",
            artifacts.tree,
        )

        self._write_json(
            output_directory / "symbols.json",
            artifacts.symbols,
        )

        self._write_json(
            output_directory / "dependencies.json",
            artifacts.dependencies,
        )

        graph_storage = GraphStorage(
            output_directory / "graph.json"
        )

        graph_storage.save(
            artifacts.graph
        )

        return artifacts

    @staticmethod
    def _write_json(
        file_path: Path,
        payload: dict[str, Any],
    ) -> None:
        import json

        with file_path.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                ensure_ascii=False,
            )


def build_repository_index(
    project_root: str | Path,
) -> RepositoryArtifacts:
    indexer = RepositoryIndexer(
        project_root
    )

    return indexer.build()


def persist_repository_index(
    project_root: str | Path,
    output_directory: str | Path,
) -> RepositoryArtifacts:
    indexer = RepositoryIndexer(
        project_root
    )

    return indexer.persist(
        output_directory
    )