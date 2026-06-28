# File: cortexfeed/knowledge/graph/v3/execution_graph.py

from __future__ import annotations

from .models import KnowledgeGraphV3


class ExecutionGraphBuilder:
    def build(
        self,
        graph: KnowledgeGraphV3,
    ) -> KnowledgeGraphV3:
        return graph