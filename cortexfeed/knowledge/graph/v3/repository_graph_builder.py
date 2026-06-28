# File: cortexfeed/knowledge/graph/v3/repository_graph_builder.py

from __future__ import annotations

from pathlib import Path

from cortexfeed.knowledge.graph.v3.graph_builder_v3 import (
    GraphBuilderV3,
)
from cortexfeed.knowledge.graph.v3.repository_graph_context import (
    RepositoryGraphContext,
)
from cortexfeed.knowledge.indexing.project_tree import (
    build_project_tree,
)
from cortexfeed.knowledge.indexing.route_index import (
    build_route_index,
)
from cortexfeed.knowledge.indexing.symbol_index import (
    build_symbol_index,
)


class RepositoryGraphBuilder:
    """
    Builds a complete RepositoryGraphContext.

    Repository
        ↓
    Project Tree
        ↓
    Symbol Index
        ↓
    Route Index
        ↓
    KnowledgeGraphV3
        ↓
    RepositoryGraphContext
    """

    def __init__(self) -> None:
        self._graph_builder = GraphBuilderV3()

    def build(
        self,
        project_root: str | Path,
    ) -> RepositoryGraphContext:
        project_root = Path(project_root)

        project_tree = build_project_tree(
            project_root,
        )

        symbols = build_symbol_index(
            project_root,
        )

        routes = build_route_index(
            project_root,
        )

        graph = self._graph_builder.build(
            project_root=project_root,
            symbol_index=symbols,
        )

        return RepositoryGraphContext(
            graph=graph,
            symbols=symbols,
            routes=routes,
            project_tree=project_tree,
        )