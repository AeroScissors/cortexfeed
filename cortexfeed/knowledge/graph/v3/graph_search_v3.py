# File: cortexfeed/knowledge/graph/v3/graph_search_v3.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from cortexfeed.knowledge.graph.v3.call_models import CallRelationship
from cortexfeed.knowledge.graph.v3.execution_search import ExecutionSearch
from cortexfeed.knowledge.graph.v3.repository_graph_context import (
    RepositoryGraphContext,
)


@dataclass(slots=True)
class SearchNode:
    id: str
    name: str
    type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class GraphSearchV3:
    """
    Drop-in replacement for GraphSearchV2, backed by RepositoryGraphContext.

    Capabilities use:
        find_node(name)           -> SearchNode | None
        find_callers(name)        -> list[SearchNode]
        find_callees(name)        -> list[SearchNode]
        trace_call_chain(name)    -> list[SearchNode]
        route_trace(method, path) -> list[SearchNode]
        impact_analysis(name)     -> dict[str, list[str]]
    """

    def __init__(self, context: RepositoryGraphContext) -> None:
        self._context = context
        self._search = ExecutionSearch()
        self._relationships: list[CallRelationship] = self._extract_relationships()
        self._route_map: dict[str, str] = self._build_route_map()

    def _extract_relationships(self) -> list[CallRelationship]:
        relationships: list[CallRelationship] = []
        for edge in self._context.graph.edges:
            relationships.append(
                CallRelationship(
                    caller_symbol=edge.source,
                    callee_symbol=edge.target,
                    caller_file="",
                    callee_file="",
                    line_number=0,
                )
            )
        return relationships

    def _build_route_map(self) -> dict[str, str]:
        route_map: dict[str, str] = {}
        routes_index = self._context.routes or {}

        # build_route_index returns a flat dict:
        # {"project": str, "route_count": int, "routes": [...]}
        # NOT a file-keyed dict, so we read the top-level "routes" list directly.
        routes_list = routes_index.get("routes", [])

        for route in routes_list:
            if not isinstance(route, dict):
                continue
            method = route.get("method", "GET").upper()
            path = route.get("path", "")
            handler = route.get("handler", "")
            if path and handler:
                route_map[f"{method}:{path}"] = handler

        return route_map

    def _symbol_to_node(self, symbol: str) -> SearchNode:
        node_type = "method" if "." in symbol else "function"
        return SearchNode(id=symbol, name=symbol, type=node_type)

    def _all_known_symbols(self) -> set[str]:
        known: set[str] = set()
        for rel in self._relationships:
            known.add(rel.caller_symbol)
            known.add(rel.callee_symbol)
        return known

    def find_node(self, name: str) -> SearchNode | None:
        if name in self._all_known_symbols():
            return self._symbol_to_node(name)
        symbols = self._context.symbols or {}
        for file_data in symbols.get("files", []):
            for method in file_data.get("methods", []):
                symbol = f"{method.get('class_name', '')}.{method.get('name', '')}"
                if method.get("name") == name or symbol == name:
                    return SearchNode(
                        id=symbol,
                        name=name,
                        type="method",
                        metadata={"file": file_data.get("file_path", "")},
                    )
        return None

    def find_callers(self, symbol_name: str) -> list[SearchNode]:
        callers = self._search.find_callers(
            relationships=self._relationships,
            symbol=symbol_name,
        )
        return [self._symbol_to_node(s) for s in callers]

    def find_callees(self, symbol_name: str) -> list[SearchNode]:
        callees = self._search.find_callees(
            relationships=self._relationships,
            symbol=symbol_name,
        )
        return [self._symbol_to_node(s) for s in callees]

    def trace_call_chain(self, start: str, max_depth: int = 10) -> list[SearchNode]:
        visited: set[str] = {start}
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        result: list[SearchNode] = []
        while queue:
            symbol, depth = queue.popleft()
            if depth >= max_depth:
                continue
            callees = self._search.find_callees(
                relationships=self._relationships,
                symbol=symbol,
            )
            for callee in callees:
                if callee not in visited:
                    visited.add(callee)
                    result.append(self._symbol_to_node(callee))
                    queue.append((callee, depth + 1))
        return result

    def route_trace(self, method: str, path: str) -> list[SearchNode]:
        route_key = f"{method.upper()}:{path}"
        entrypoint = self._route_map.get(route_key)
        if not entrypoint:
            return []
        chain = self.trace_call_chain(entrypoint)
        return [self._symbol_to_node(entrypoint), *chain]

    def impact_analysis(self, symbol_name: str) -> dict[str, list[str]]:
        callers = self._search.find_callers(
            relationships=self._relationships,
            symbol=symbol_name,
        )
        callees = self._search.find_callees(
            relationships=self._relationships,
            symbol=symbol_name,
        )
        visited: set[str] = {symbol_name}
        queue: deque[str] = deque(callers)
        dependents: list[str] = []
        while queue:
            sym = queue.popleft()
            if sym in visited:
                continue
            visited.add(sym)
            dependents.append(sym)
            upstream = self._search.find_callers(
                relationships=self._relationships,
                symbol=sym,
            )
            queue.extend(upstream)
        return {"callers": callers, "callees": callees, "dependents": dependents}