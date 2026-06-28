# File: cortexfeed/knowledge/graph/v3/repository_query_service.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.repository_question_engine import (
    RepositoryQuestionEngine,
)


class RepositoryQueryService:
    """
    User-facing query layer for repository intelligence.
    """

    def __init__(self) -> None:
        self._engine = RepositoryQuestionEngine()

    def who_calls(
        self,
        relationships: list[CallRelationship],
        symbol: str,
    ) -> list[str]:
        return self._engine.who_calls(
            relationships=relationships,
            symbol=symbol,
        )

    def trace(
        self,
        relationships: list[CallRelationship],
        start: str,
        target: str,
    ) -> list[str]:
        return self._engine.trace(
            relationships=relationships,
            start=start,
            target=target,
        )