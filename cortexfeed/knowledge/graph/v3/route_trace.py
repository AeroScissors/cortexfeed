# File: cortexfeed/knowledge/graph/v3/route_trace.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.execution_trace import (
    ExecutionTraceBuilder,
)


class RouteTraceBuilder:
    """
    Builds execution traces starting from a route.

    Example:

    POST /login
        ↓
    AuthController.login
        ↓
    AuthService.login
        ↓
    UserRepository.find_user
    """

    def __init__(self) -> None:
        self._trace_builder = ExecutionTraceBuilder()

    def trace(
        self,
        route_map: dict[str, str],
        relationships: list[CallRelationship],
        route: str,
        target: str,
    ) -> list[str]:
        if route not in route_map:
            return []

        entrypoint = route_map[route]

        execution_trace = self._trace_builder.trace(
            relationships=relationships,
            start=entrypoint,
            target=target,
        )

        if not execution_trace:
            return []

        return [
            route,
            *execution_trace,
        ]