# File: cortexfeed/knowledge/graph/v3/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    ROUTE = "route"
    IMPORT = "import"
    CALL_SITE = "call_site"


class EdgeType(str, Enum):
    IMPORTS = "imports"
    DEPENDS_ON = "depends_on"
    CALLS = "calls"
    USES = "uses"
    ROUTES_TO = "routes_to"


@dataclass(slots=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GraphEdge:
    source: str
    target: str
    edge_type: EdgeType
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeGraphV3:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)