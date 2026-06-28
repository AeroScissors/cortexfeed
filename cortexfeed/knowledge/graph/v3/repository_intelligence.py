# File: cortexfeed/knowledge/graph/v3/repository_intelligence.py

from __future__ import annotations

from pathlib import Path

from cortexfeed.knowledge.graph.v3.graph_builder_v3 import (
    GraphBuilderV3,
)
from cortexfeed.knowledge.graph.v3.repository_question_engine import (
    RepositoryQuestionEngine,
)


class RepositoryIntelligence:
    """
    Repository-aware intelligence facade.

    Repository
        ↓
    GraphBuilderV3
        ↓
    RepositoryQuestionEngine
    """

    def __init__(self) -> None:
        self._graph_builder = GraphBuilderV3()
        self._engine = RepositoryQuestionEngine()

    def build_graph(
        self,
        project_root: Path,
    ):
        return self._graph_builder.build(
            project_root=project_root,
        )

    @property
    def engine(
        self,
    ) -> RepositoryQuestionEngine:
        return self._engine