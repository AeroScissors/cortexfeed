# File: cortexfeed/knowledge/graph/symbol_graph.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class GraphNode:
    """
    Base graph node.
    """

    id: str
    node_type: str
    name: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "name": self.name,
            "metadata": self.metadata,
        }


@dataclass(slots=True, frozen=True)
class FileNode(GraphNode):
    """
    Repository file node.
    """

    path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_type",
            "file",
        )

    @classmethod
    def create(
        cls,
        *,
        path: str,
    ) -> "FileNode":
        return cls(
            id=path,
            node_type="file",
            name=path.split("/")[-1],
            path=path,
        )


@dataclass(slots=True, frozen=True)
class DirectoryNode(GraphNode):
    """
    Repository directory node.
    """

    path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_type",
            "directory",
        )

    @classmethod
    def create(
        cls,
        *,
        path: str,
        name: str,
    ) -> "DirectoryNode":
        return cls(
            id=path,
            node_type="directory",
            name=name,
            path=path,
        )


@dataclass(slots=True, frozen=True)
class ClassNode(GraphNode):
    """
    Class symbol node.
    """

    file_path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_type",
            "class",
        )

    @classmethod
    def create(
        cls,
        *,
        file_path: str,
        class_name: str,
        metadata: dict[str, Any],
    ) -> "ClassNode":
        return cls(
            id=f"{file_path}::class::{class_name}",
            node_type="class",
            name=class_name,
            file_path=file_path,
            metadata=metadata,
        )


@dataclass(slots=True, frozen=True)
class FunctionNode(GraphNode):
    """
    Function symbol node.
    """

    file_path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_type",
            "function",
        )

    @classmethod
    def create(
        cls,
        *,
        file_path: str,
        function_name: str,
        metadata: dict[str, Any],
    ) -> "FunctionNode":
        return cls(
            id=f"{file_path}::function::{function_name}",
            node_type="function",
            name=function_name,
            file_path=file_path,
            metadata=metadata,
        )


@dataclass(slots=True, frozen=True)
class MethodNode(GraphNode):
    """
    Method symbol node.
    """

    file_path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_type",
            "method",
        )

    @classmethod
    def create(
        cls,
        *,
        file_path: str,
        class_name: str,
        method_name: str,
        metadata: dict[str, Any],
    ) -> "MethodNode":
        return cls(
            id=(
                f"{file_path}"
                f"::method::"
                f"{class_name}.{method_name}"
            ),
            node_type="method",
            name=method_name,
            file_path=file_path,
            metadata=metadata,
        )


@dataclass(slots=True, frozen=True)
class RouteNode(GraphNode):
    """
    Route endpoint node.
    """

    file_path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_type",
            "route",
        )

    @classmethod
    def create(
        cls,
        *,
        file_path: str,
        method: str,
        route_path: str,
        metadata: dict[str, Any],
    ) -> "RouteNode":
        return cls(
            id=(
                f"{file_path}"
                f"::route::"
                f"{method}::{route_path}"
            ),
            node_type="route",
            name=route_path,
            file_path=file_path,
            metadata=metadata,
        )


@dataclass(slots=True, frozen=True)
class DependencyNode(GraphNode):
    """
    Dependency/import node.
    """

    module_name: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_type",
            "dependency",
        )

    @classmethod
    def create(
        cls,
        *,
        module_name: str,
    ) -> "DependencyNode":
        return cls(
            id=f"dependency::{module_name}",
            node_type="dependency",
            name=module_name,
            module_name=module_name,
        )


@dataclass(slots=True, frozen=True)
class GraphEdge:
    """
    Directed graph edge.
    """

    source: str
    target: str
    relationship: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
        }


@dataclass(slots=True)
class SymbolGraph:
    """
    Strongly typed graph model.

    Used by:

    - GraphBuilder
    - GraphStorage
    - GraphSearch
    - DependencyResolver
    - Investigation V3
    """

    nodes: dict[str, GraphNode] = field(
        default_factory=dict
    )

    edges: list[GraphEdge] = field(
        default_factory=list
    )

    def add_node(
        self,
        node: GraphNode,
    ) -> None:
        self.nodes[node.id] = node

    def add_edge(
        self,
        edge: GraphEdge,
    ) -> None:
        self.edges.append(edge)

    def get_node(
        self,
        node_id: str,
    ) -> GraphNode | None:
        return self.nodes.get(node_id)

    def neighbors(
        self,
        node_id: str,
    ) -> list[GraphNode]:
        results: list[GraphNode] = []

        for edge in self.edges:
            if edge.source != node_id:
                continue

            target = self.nodes.get(
                edge.target
            )

            if target is not None:
                results.append(target)

        return results

    def node_count(
        self,
    ) -> int:
        return len(self.nodes)

    def edge_count(
        self,
    ) -> int:
        return len(self.edges)

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "nodes": [
                node.to_dict()
                for node in self.nodes.values()
            ],
            "edges": [
                edge.to_dict()
                for edge in self.edges
            ],
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
        }