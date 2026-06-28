# File: cortexfeed/knowledge/graph/v3/repository_query_api.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.query_executor import (
    QueryExecutor,
)
from cortexfeed.knowledge.graph.v3.query_parser import (
    QueryParser,
)


class RepositoryQueryAPI:
    """
    Public repository intelligence query interface.

    Question
        ↓
    QueryParser
        ↓
    QueryIntent
        ↓
    QueryExecutor
        ↓
    Answer
    """

    def __init__(self) -> None:
        self._parser = QueryParser()
        self._executor = QueryExecutor()

    def query(
        self,
        question: str,
        relationships: list[CallRelationship],
    ):
        intent = self._parser.parse(
            question,
        )

        return self._executor.execute(
            intent=intent,
            relationships=relationships,
        )