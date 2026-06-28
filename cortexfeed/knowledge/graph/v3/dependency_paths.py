# File: cortexfeed/knowledge/graph/v3/dependency_paths.py

from __future__ import annotations

from .models import KnowledgeGraphV3


class DependencyPathBuilder:
    def build(
        self,
        graph: KnowledgeGraphV3,
    ) -> KnowledgeGraphV3:
        return graph