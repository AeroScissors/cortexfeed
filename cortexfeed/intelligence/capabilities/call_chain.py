# File: cortexfeed/intelligence/capabilities/call_chain.py

from __future__ import annotations

from cortexfeed.intelligence.capabilities.models import (
    CapabilityResult,
)
from cortexfeed.knowledge.graph.v3.graph_search_v3 import (
    GraphSearchV3,
)


class CallChainCapability:
    def __init__(self, graph_search: GraphSearchV3) -> None:
        self.graph_search = graph_search

    def execute(self, symbol_name: str, max_depth: int = 10) -> CapabilityResult:
        node = self.graph_search.find_node(symbol_name)

        if not node:
            return CapabilityResult(
                capability="call_chain",
                confidence=0.0,
                summary=f"Symbol '{symbol_name}' was not found.",
                symbols=[symbol_name],
            )

        chain_nodes = self.graph_search.trace_call_chain(symbol_name, max_depth=max_depth)
        execution_path = [symbol_name, *[n.name for n in chain_nodes]]

        return CapabilityResult(
            capability="call_chain",
            confidence=0.95,
            summary=f"Execution chain for '{symbol_name}' contains {len(execution_path)} nodes.",
            symbols=execution_path,
            execution_path=execution_path,
            metadata={
                "root_symbol": symbol_name,
                "depth": max_depth,
                "chain_length": len(execution_path),
            },
        )