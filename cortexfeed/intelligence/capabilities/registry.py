# File: cortexfeed/intelligence/capabilities/registry.py

from __future__ import annotations

from cortexfeed.intelligence.capabilities.call_chain import (
    CallChainCapability,
)
from cortexfeed.intelligence.capabilities.impact_analysis import (
    ImpactAnalysisCapability,
)
from cortexfeed.intelligence.capabilities.route_trace import (
    RouteTraceCapability,
)
from cortexfeed.intelligence.capabilities.where_is_symbol import (
    WhereIsSymbolCapability,
)


class CapabilityRegistry:
    def __init__(
        self,
        graph_search,
    ) -> None:
        self._capabilities = {
            "where_is_symbol": WhereIsSymbolCapability(
                graph_search,
            ),
            "route_trace": RouteTraceCapability(
                graph_search,
            ),
            "impact_analysis": ImpactAnalysisCapability(
                graph_search,
            ),
            "call_chain": CallChainCapability(
                graph_search,
            ),
        }

    def get(
        self,
        capability_name: str,
    ):
        return self._capabilities.get(
            capability_name,
        )

    def list_capabilities(
        self,
    ) -> list[str]:
        return sorted(
            self._capabilities.keys(),
        )