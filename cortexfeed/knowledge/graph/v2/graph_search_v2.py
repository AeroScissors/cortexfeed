# File: cortexfeed/knowledge/graph/v2/graph_search_v2.py
from __future__ import annotations

from collections import deque
from typing import Any

from cortexfeed.knowledge.models import Graph, GraphNode


class GraphSearchV2:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        
        # Internal Indexes
        self.nodes_by_id: dict[str, GraphNode] = {}
        self.nodes_by_name: dict[str, GraphNode] = {}
        self.outgoing_edges: dict[str, list[Any]] = {}
        self.incoming_edges: dict[str, list[Any]] = {}

        # Build indexes once
        for node in self.graph.nodes:
            self.nodes_by_id[node.id] = node
            self.outgoing_edges[node.id] = []
            self.incoming_edges[node.id] = []

            existing = self.nodes_by_name.get(node.name)

            if existing is None:
                self.nodes_by_name[node.name] = node
            elif (
                existing.type == "EXTERNAL_SYMBOL"
                and node.type != "EXTERNAL_SYMBOL"
            ):
                self.nodes_by_name[node.name] = node

        for edge in self.graph.edges:
            if edge.source not in self.outgoing_edges:
                self.outgoing_edges[edge.source] = []
            if edge.target not in self.incoming_edges:
                self.incoming_edges[edge.target] = []
                
            self.outgoing_edges[edge.source].append(edge)
            self.incoming_edges[edge.target].append(edge)

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    def _get_outgoing(self, node_id: str, edge_types: list[str] | None = None) -> list[GraphNode]:
        edges = self.outgoing_edges.get(node_id, [])
        if edge_types:
            edges = [e for e in edges if e.relationship in edge_types]
        return [self.nodes_by_id[e.target] for e in edges if e.target in self.nodes_by_id]

    def _get_incoming(self, node_id: str, edge_types: list[str] | None = None) -> list[GraphNode]:
        edges = self.incoming_edges.get(node_id, [])
        if edge_types:
            edges = [e for e in edges if e.relationship in edge_types]
        return [self.nodes_by_id[e.source] for e in edges if e.source in self.nodes_by_id]

    def _bfs(self, start_id: str, direction: str, edge_types: list[str] | None, max_depth: int) -> list[GraphNode]:
        visited = {start_id}
        queue = deque([(start_id, 0)])
        result = []

        while queue:
            current_id, depth = queue.popleft()
            
            if current_id != start_id and current_id in self.nodes_by_id:
                result.append(self.nodes_by_id[current_id])

            if depth >= max_depth:
                continue

            if direction == "outgoing":
                next_nodes = self._get_outgoing(current_id, edge_types)
            else:
                next_nodes = self._get_incoming(current_id, edge_types)

            for node in next_nodes:
                if node.id not in visited:
                    visited.add(node.id)
                    queue.append((node.id, depth + 1))

        return result

    def _dfs(self, start_id: str, direction: str, edge_types: list[str] | None, max_depth: int) -> list[GraphNode]:
        visited = set()
        result = []

        def traverse(current_id: str, depth: int) -> None:
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            if current_id != start_id and current_id in self.nodes_by_id:
                result.append(self.nodes_by_id[current_id])

            if depth >= max_depth:
                return

            if direction == "outgoing":
                next_nodes = self._get_outgoing(current_id, edge_types)
            else:
                next_nodes = self._get_incoming(current_id, edge_types)

            for node in next_nodes:
                if node.id not in visited:
                    traverse(node.id, depth + 1)

        traverse(start_id, 0)
        return result

    # ------------------------------------------------------------------
    # Core Queries
    # ------------------------------------------------------------------

    def find_node(self, name: str) -> GraphNode | None:
        """Find a node by its exact name."""
        return self.nodes_by_name.get(name)

    def get_dependencies(self, node_id: str) -> list[GraphNode]:
        """Get all immediate outgoing relationships."""
        return self._get_outgoing(node_id)

    def get_dependents(self, node_id: str) -> list[GraphNode]:
        """Get all immediate incoming relationships."""
        return self._get_incoming(node_id)

    def find_callers(self, function_name: str) -> list[GraphNode]:
        """Find immediate callers of a specific function or method."""
        node = self.find_node(function_name)
        if not node:
            return []
        return self._get_incoming(node.id, edge_types=["CALLS"])

    def find_callees(self, function_name: str) -> list[GraphNode]:
        """Find immediate functions called by a specific function or method."""
        node = self.find_node(function_name)
        if not node:
            return []
        return self._get_outgoing(node.id, edge_types=["CALLS"])

    def trace_call_chain(self, start: str, max_depth: int = 10) -> list[GraphNode]:
        """Trace outgoing call chain breadth-first to max depth."""
        node = self.find_node(start)
        if not node:
            return []
        return self._bfs(node.id, direction="outgoing", edge_types=["CALLS"], max_depth=max_depth)

    def trace_callers(self, target: str, max_depth: int = 10) -> list[GraphNode]:
        """Trace incoming call chain (upstream callers) breadth-first to max depth."""
        node = self.find_node(target)
        if not node:
            return []
        return self._bfs(node.id, direction="incoming", edge_types=["CALLS"], max_depth=max_depth)

    def inheritance_tree(self, class_name: str) -> list[GraphNode]:
        """Find both parent classes and child classes for a given class."""
        node = self.find_node(class_name)
        if not node:
            return []
        parents = self._bfs(node.id, direction="outgoing", edge_types=["INHERITS"], max_depth=100)
        children = self._bfs(node.id, direction="incoming", edge_types=["INHERITS"], max_depth=100)
        # Deduplicate while preserving order
        seen = set()
        tree = []
        for n in parents + children:
            if n.id not in seen:
                seen.add(n.id)
                tree.append(n)
        return tree

    def route_trace(self, method: str, path: str) -> list[GraphNode]:
        """Trace dependencies triggered by an API route."""
        route_name = f"{method.upper()}:{path}"
        node = self.find_node(route_name)
        if not node:
            return []
        # Trace all outgoing execution edges from the route
        return self._bfs(
            node.id, 
            direction="outgoing", 
            edge_types=["CALLS", "REFERENCES", "INSTANTIATES"], 
            max_depth=10
        )

    def impact_analysis(self, symbol_name: str) -> dict[str, list[str]]:
        """Return a structured analysis of a symbol's graph impact."""
        node = self.find_node(symbol_name)
        if not node:
            return {
                "callers": [],
                "callees": [],
                "dependencies": [],
                "dependents": []
            }

        return {
            "callers": [n.name for n in self.find_callers(symbol_name)],
            "callees": [n.name for n in self.find_callees(symbol_name)],
            "dependencies": [n.name for n in self.get_dependencies(node.id)],
            "dependents": [n.name for n in self.get_dependents(node.id)]
        }

    def repository_context(self, symbol_name: str) -> dict[str, object]:
        """Returns the primary Investigation V3 graph context for a symbol."""
        node = self.find_node(symbol_name)
        if not node:
            return {}

        return {
            "node": {
                "id": node.id,
                "type": node.type,
                "name": node.name,
            },
            "dependencies": [n.name for n in self.get_dependencies(node.id)],
            "dependents": [n.name for n in self.get_dependents(node.id)],
            "callers": [n.name for n in self.find_callers(symbol_name)],
            "callees": [n.name for n in self.find_callees(symbol_name)],
            "inheritance": [n.name for n in self.inheritance_tree(symbol_name)],
        }