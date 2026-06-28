# File: cortexfeed/tests/knowledge/test_repository_graph_context.py

from cortexfeed.knowledge.graph.v3.models import (
    KnowledgeGraphV3,
)
from cortexfeed.knowledge.graph.v3.repository_graph_context import (
    RepositoryGraphContext,
)


def test_context_creation() -> None:
    context = RepositoryGraphContext(
        graph=KnowledgeGraphV3(),
        symbols={},
        routes={},
        project_tree={},
    )

    assert context.graph is not None
    assert context.symbols == {}
    assert context.routes == {}
    assert context.project_tree == {}