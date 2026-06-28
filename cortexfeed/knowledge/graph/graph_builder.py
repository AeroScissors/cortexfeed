# File: cortexfeed/knowledge/graph/graph_builder.py

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

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
class GraphNode:
    id: str
    node_type: str
    name: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class GraphEdge:
    source: str
    target: str
    relationship: str


class GraphBuilder:
    """
    Builds the repository intelligence graph.

    Graph contains:

    - file nodes
    - class nodes
    - function nodes
    - method nodes
    - route nodes

    Relationships:

    - contains
    - imports
    - defines
    - exposes_route
    """

    def __init__(
        self,
        project_root: str | Path,
    ) -> None:
        self.project_root = Path(project_root).resolve()

        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project not found: {self.project_root}"
            )

    def build(self) -> dict[str, Any]:
        tree = build_project_tree(
            self.project_root
        )

        symbols = build_symbol_index(
            self.project_root
        )

        dependencies = resolve_dependencies(
            self.project_root
        )

        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        self._create_file_nodes(
            tree,
            nodes,
        )

        self._create_symbol_nodes(
            symbols,
            nodes,
            edges,
        )

        self._create_dependency_edges(
            dependencies,
            edges,
        )

        return {
            "project": self.project_root.name,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": [
                asdict(node)
                for node in sorted(
                    nodes.values(),
                    key=lambda item: item.id,
                )
            ],
            "edges": [
                asdict(edge)
                for edge in sorted(
                    edges,
                    key=lambda item: (
                        item.source,
                        item.target,
                        item.relationship,
                    ),
                )
            ],
        }

    def _create_file_nodes(
        self,
        tree: dict[str, Any],
        nodes: dict[str, GraphNode],
    ) -> None:
        def walk(
            current: dict[str, Any],
        ) -> None:
            path = current["path"]

            nodes[path] = GraphNode(
                id=path,
                node_type=current["node_type"],
                name=current["name"],
            )

            for child in current.get(
                "children",
                [],
            ):
                walk(child)

        walk(tree)

    def _create_symbol_nodes(
        self,
        symbols: dict[str, Any],
        nodes: dict[str, GraphNode],
        edges: list[GraphEdge],
    ) -> None:
        for file_data in symbols["files"]:
            file_path = file_data["file_path"]

            for class_data in file_data["classes"]:
                symbol_id = (
                    f"{file_path}::"
                    f"class::{class_data['name']}"
                )

                nodes[symbol_id] = GraphNode(
                    id=symbol_id,
                    node_type="class",
                    name=class_data["name"],
                    metadata=class_data,
                )

                edges.append(
                    GraphEdge(
                        source=file_path,
                        target=symbol_id,
                        relationship="defines",
                    )
                )

            for function_data in file_data[
                "functions"
            ]:
                symbol_id = (
                    f"{file_path}::"
                    f"function::{function_data['name']}"
                )

                nodes[symbol_id] = GraphNode(
                    id=symbol_id,
                    node_type="function",
                    name=function_data["name"],
                    metadata=function_data,
                )

                edges.append(
                    GraphEdge(
                        source=file_path,
                        target=symbol_id,
                        relationship="defines",
                    )
                )

            for method_data in file_data[
                "methods"
            ]:
                symbol_id = (
                    f"{file_path}::"
                    f"method::"
                    f"{method_data['class_name']}."
                    f"{method_data['name']}"
                )

                nodes[symbol_id] = GraphNode(
                    id=symbol_id,
                    node_type="method",
                    name=method_data["name"],
                    metadata=method_data,
                )

                edges.append(
                    GraphEdge(
                        source=file_path,
                        target=symbol_id,
                        relationship="defines",
                    )
                )

            for route_data in file_data[
                "routes"
            ]:
                route_id = (
                    f"{file_path}::route::"
                    f"{route_data['method']}::"
                    f"{route_data['path']}"
                )

                nodes[route_id] = GraphNode(
                    id=route_id,
                    node_type="route",
                    name=route_data["path"],
                    metadata=route_data,
                )

                edges.append(
                    GraphEdge(
                        source=file_path,
                        target=route_id,
                        relationship="exposes_route",
                    )
                )

    def _create_dependency_edges(
        self,
        dependencies: dict[str, Any],
        edges: list[GraphEdge],
    ) -> None:
        for dependency in dependencies[
            "file_dependencies"
        ]:
            edges.append(
                GraphEdge(
                    source=dependency[
                        "source_file"
                    ],
                    target=dependency[
                        "target_file"
                    ],
                    relationship="imports",
                )
            )


def build_graph(
    project_root: str | Path,
) -> dict[str, Any]:
    builder = GraphBuilder(project_root)

    return builder.build()