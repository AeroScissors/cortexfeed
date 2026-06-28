# File: cortexfeed/knowledge/graph/v3/query_executor.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.query_models import (
    QueryIntent,
)
from cortexfeed.knowledge.graph.v3.repository_question_engine import (
    RepositoryQuestionEngine,
)


class QueryExecutor:
    """
    Executes repository query intents against
    the repository intelligence engine.
    """

    def __init__(self) -> None:
        self._engine = RepositoryQuestionEngine()

    def execute(
        self,
        intent: QueryIntent,
        relationships: list[CallRelationship],
    ):
        if intent.intent_type == "who_calls":
            return self._engine.who_calls(
                relationships=relationships,
                symbol=intent.symbol or "",
            )

        if intent.intent_type == "what_does_call":
            return self._engine.what_does_call(
                relationships=relationships,
                symbol=intent.symbol or "",
            )

        if intent.intent_type == "can_reach":
            return self._engine.can_reach(
                relationships=relationships,
                start=intent.start or "",
                target=intent.target or "",
            )

        if intent.intent_type == "trace":
            return self._engine.trace(
                relationships=relationships,
                start=intent.start or "",
                target=intent.target or "",
            )

        return None