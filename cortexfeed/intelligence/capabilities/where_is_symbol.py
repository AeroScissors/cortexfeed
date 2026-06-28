# File: cortexfeed/intelligence/capabilities/where_is_symbol.py

from __future__ import annotations

from cortexfeed.intelligence.capabilities.models import (
    CapabilityResult,
)
from cortexfeed.knowledge.graph.v3.graph_search_v3 import (
    GraphSearchV3,
)


class WhereIsSymbolCapability:
    def __init__(self, graph_search: GraphSearchV3) -> None:
        self.graph_search = graph_search

    def execute(self, symbol_name: str) -> CapabilityResult:
        node = self.graph_search.find_node(symbol_name)

        if not node:
            return CapabilityResult(
                capability="where_is_symbol",
                confidence=0.0,
                summary=f"Symbol '{symbol_name}' was not found.",
            )

        callers = [n.name for n in self.graph_search.find_callers(symbol_name)]
        callees = [n.name for n in self.graph_search.find_callees(symbol_name)]

        return CapabilityResult(
            capability="where_is_symbol",
            confidence=0.95,
            summary=f"{symbol_name} is a {node.type.lower()}.",
            symbols=[symbol_name],
            callers=callers,
            callees=callees,
            metadata={"node_id": node.id, "node_type": node.type},
        )