# File: cortexfeed/intelligence/capabilities/impact_analysis.py

from __future__ import annotations

from cortexfeed.intelligence.capabilities.models import (
    CapabilityResult,
)
from cortexfeed.knowledge.graph.v3.graph_search_v3 import (
    GraphSearchV3,
)


class ImpactAnalysisCapability:
    def __init__(self, graph_search: GraphSearchV3) -> None:
        self.graph_search = graph_search

    def execute(self, symbol_name: str) -> CapabilityResult:
        impact = self.graph_search.impact_analysis(symbol_name)

        if not any(impact.values()):
            return CapabilityResult(
                capability="impact_analysis",
                confidence=0.0,
                summary=f"No impact information found for '{symbol_name}'.",
                symbols=[symbol_name],
            )

        dependents = impact.get("dependents", [])
        callers = impact.get("callers", [])
        callees = impact.get("callees", [])
        risk_score = len(dependents) + len(callers) + len(callees)

        return CapabilityResult(
            capability="impact_analysis",
            confidence=0.90,
            summary=f"{symbol_name} affects {risk_score} related symbols.",
            symbols=[symbol_name],
            callers=callers,
            callees=callees,
            metadata={"risk_score": risk_score, "dependents": dependents},
        )