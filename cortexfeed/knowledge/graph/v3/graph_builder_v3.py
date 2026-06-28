# File: cortexfeed/knowledge/graph/v3/graph_builder_v3.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from cortexfeed.knowledge.graph.v3.call_graph import (
    CallGraphBuilder,
)
from cortexfeed.knowledge.graph.v3.models import (
    KnowledgeGraphV3,
)
from cortexfeed.knowledge.graph.v3.resolvers.caller_resolver import (
    CallerResolver,
)
from cortexfeed.knowledge.indexing.symbol_index import (
    build_symbol_index,
)


class GraphBuilderV3:
    def __init__(self) -> None:
        self._caller_resolver = CallerResolver()
        self._call_graph_builder = CallGraphBuilder()

    def build(
        self,
        project_root: Path,
        symbol_index: dict[str, Any] | None = None,
        import_index: dict[str, Any] | None = None,
    ) -> KnowledgeGraphV3:
        graph = KnowledgeGraphV3()

        if symbol_index is None:
            symbol_index = build_symbol_index(
                project_root,
            )

        if import_index is None:
            import_index = {}

        relationships = self._caller_resolver.resolve(
            project_root=project_root,
            symbol_index=symbol_index,
            import_index=import_index,
        )

        call_edges = self._call_graph_builder.build(
            relationships,
        )

        graph.edges.extend(
            call_edges,
        )

        return graph