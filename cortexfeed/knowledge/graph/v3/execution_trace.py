# File: cortexfeed/knowledge/graph/v3/execution_trace.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.traversal.path_finder import (
    PathFinder,
)


class ExecutionTraceBuilder:
    """
    Builds execution traces from resolved call relationships.

    Example:

    Controller.login
        ↓
    AuthService.login
        ↓
    UserRepository.find_user
    """

    def __init__(self) -> None:
        self._path_finder = PathFinder()

    def trace(
        self,
        relationships: list[CallRelationship],
        start: str,
        target: str,
    ) -> list[str]:
        adjacency = self._build_adjacency(
            relationships,
        )

        return self._path_finder.shortest_path(
            adjacency=adjacency,
            start=start,
            target=target,
        )

    def _build_adjacency(
        self,
        relationships: list[CallRelationship],
    ) -> dict[str, list[str]]:
        adjacency: dict[str, list[str]] = {}

        for relationship in relationships:
            adjacency.setdefault(
                relationship.caller_symbol,
                [],
            ).append(
                relationship.callee_symbol,
            )

            adjacency.setdefault(
                relationship.callee_symbol,
                [],
            )

        return adjacency