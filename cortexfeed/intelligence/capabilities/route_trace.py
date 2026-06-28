# File: cortexfeed/intelligence/capabilities/route_trace.py

from __future__ import annotations

from cortexfeed.intelligence.capabilities.models import (
    CapabilityResult,
)
from cortexfeed.knowledge.graph.v3.graph_search_v3 import (
    GraphSearchV3,
)


class RouteTraceCapability:
    def __init__(self, graph_search: GraphSearchV3) -> None:
        self.graph_search = graph_search

    def execute(self, method: str, path: str) -> CapabilityResult:
        route_name = f"{method.upper()}:{path}"
        execution_nodes = self.graph_search.route_trace(method, path)

        if not execution_nodes:
            return CapabilityResult(
                capability="route_trace",
                confidence=0.0,
                summary=f"Route '{route_name}' was not found.",
                routes=[route_name],
            )

        execution_path = [node.name for node in execution_nodes]

        return CapabilityResult(
            capability="route_trace",
            confidence=0.95,
            summary=f"Route '{route_name}' resolved to an execution path of {len(execution_path)} nodes.",
            routes=[route_name],
            symbols=execution_path,
            execution_path=execution_path,
            metadata={"route": route_name, "path_length": len(execution_path)},
        )