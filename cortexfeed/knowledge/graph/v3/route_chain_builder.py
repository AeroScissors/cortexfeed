# File: cortexfeed/knowledge/graph/v3/route_chain_builder.py

from __future__ import annotations

from .models import KnowledgeGraphV3


class RouteChainBuilder:
    def build(
        self,
        graph: KnowledgeGraphV3,
    ) -> KnowledgeGraphV3:
        return graph