# File: cortexfeed/knowledge/projects/loader.py

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.graph.graph_builder import (
    build_graph,
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
class ProjectMetadata:
    project_name: str
    project_path: str
    indexed_at: str
    file_count: int
    directory_count: int
    symbol_count: int
    graph_nodes: int
    graph_edges: int


class ProjectLoader:
    """
    Main Project Intelligence pipeline.

    Responsibilities:

    1. Scan repository
    2. Build tree
    3. Extract symbols
    4. Resolve dependencies
    5. Build graph
    6. Persist artifacts

    Output:

    data/projects/<project_name>/
        tree.json
        symbols.json
        graph.json
        metadata.json
    """

    def __init__(
        self,
        project_root: str | Path,
        output_root: str | Path = "data/projects",
    ) -> None:
        self.project_root = Path(project_root).resolve()

        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project not found: {self.project_root}"
            )

        self.output_root = Path(output_root)

    def load(self) -> dict[str, Any]:
        project_name = self.project_root.name

        artifact_directory = (
            self.output_root / project_name
        )

        artifact_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

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

        metadata = self._build_metadata(
            project_name=project_name,
            tree=tree,
            symbols=symbols,
            graph=graph,
        )

        self._write_json(
            artifact_directory / "tree.json",
            tree,
        )

        self._write_json(
            artifact_directory / "symbols.json",
            symbols,
        )

        self._write_json(
            artifact_directory / "graph.json",
            graph,
        )

        self._write_json(
            artifact_directory / "metadata.json",
            metadata,
        )

        return {
            "project": project_name,
            "output_directory": str(
                artifact_directory
            ),
            "tree": tree,
            "symbols": symbols,
            "dependencies": dependencies,
            "graph": graph,
            "metadata": metadata,
        }

    def _build_metadata(
        self,
        *,
        project_name: str,
        tree: dict[str, Any],
        symbols: dict[str, Any],
        graph: dict[str, Any],
    ) -> dict[str, Any]:
        file_count = 0
        directory_count = 0

        stack = [tree]

        while stack:
            current = stack.pop()

            if current["node_type"] == "file":
                file_count += 1
            else:
                directory_count += 1

            stack.extend(
                current.get("children", [])
            )

        symbol_count = 0

        for file_data in symbols["files"]:
            symbol_count += len(
                file_data["classes"]
            )
            symbol_count += len(
                file_data["functions"]
            )
            symbol_count += len(
                file_data["methods"]
            )
            symbol_count += len(
                file_data["routes"]
            )

        metadata = ProjectMetadata(
            project_name=project_name,
            project_path=str(
                self.project_root
            ),
            indexed_at=datetime.now(
                timezone.utc
            ).isoformat(),
            file_count=file_count,
            directory_count=directory_count,
            symbol_count=symbol_count,
            graph_nodes=graph["node_count"],
            graph_edges=graph["edge_count"],
        )

        return asdict(metadata)

    @staticmethod
    def _write_json(
        output_file: Path,
        payload: dict[str, Any],
    ) -> None:
        with output_file.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                ensure_ascii=False,
            )


def load_project(
    project_root: str | Path,
) -> dict[str, Any]:
    """
    Public entrypoint used by higher-level
    project management services.
    """

    loader = ProjectLoader(
        project_root=project_root,
    )

    return loader.load()