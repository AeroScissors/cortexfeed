# File: cortexfeed/intelligence/bootstrap.py

from __future__ import annotations

from pathlib import Path

from cortexfeed.intelligence.capabilities.registry import (
    CapabilityRegistry,
)
from cortexfeed.intelligence.facade import (
    RepositoryIntelligenceFacade,
)
from cortexfeed.intelligence.query_router import (
    QueryRouter,
)
from cortexfeed.intelligence.repository_service import (
    RepositoryService,
)
from cortexfeed.knowledge.graph.v3.repository_graph_builder import (
    RepositoryGraphBuilder,
)
from cortexfeed.knowledge.graph.v3.graph_search_v3 import (
    GraphSearchV3,
)


def build_repository_intelligence(
    project_root: str | Path,
) -> RepositoryIntelligenceFacade:
    project_root = Path(project_root)

    repository_context = (
        RepositoryGraphBuilder()
        .build(project_root)
    )

    graph_search = GraphSearchV3(repository_context)

    registry = CapabilityRegistry(graph_search)
    router = QueryRouter(registry)
    service = RepositoryService(router)

    return RepositoryIntelligenceFacade(service)