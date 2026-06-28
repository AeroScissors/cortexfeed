# File: cortexfeed/knowledge/graph/v3/route_intelligence.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.route_trace import (
    RouteTraceBuilder,
)


class RouteIntelligence:
    """
    Repository-aware route tracing layer.

    Provides a stable interface between:

        Route Index
            ↓
        Route Trace Builder
            ↓
        Repository Intelligence
    """

    def __init__(self) -> None:
        self._route_trace_builder = RouteTraceBuilder()

    def trace_route(
        self,
        route_map: dict[str, str],
        relationships: list[CallRelationship],
        route: str,
        target: str,
    ) -> list[str]:
        return self._route_trace_builder.trace(
            route_map=route_map,
            relationships=relationships,
            route=route,
            target=target,
        )