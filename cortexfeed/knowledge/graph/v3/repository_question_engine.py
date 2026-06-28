# File: cortexfeed/knowledge/graph/v3/repository_question_engine.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.execution_search import (
    ExecutionSearch,
)
from cortexfeed.knowledge.graph.v3.route_intelligence import (
    RouteIntelligence,
)


class RepositoryQuestionEngine:
    """
    High-level repository intelligence query engine.

    Exposes repository-aware questions using the
    underlying graph infrastructure.
    """

    def __init__(self) -> None:
        self._search = ExecutionSearch()
        self._route_intelligence = RouteIntelligence()

    def who_calls(
        self,
        relationships: list[CallRelationship],
        symbol: str,
    ) -> list[str]:
        return self._search.find_callers(
            relationships=relationships,
            symbol=symbol,
        )

    def what_does_call(
        self,
        relationships: list[CallRelationship],
        symbol: str,
    ) -> list[str]:
        return self._search.find_callees(
            relationships=relationships,
            symbol=symbol,
        )

    def can_reach(
        self,
        relationships: list[CallRelationship],
        start: str,
        target: str,
    ) -> bool:
        return self._search.has_path(
            relationships=relationships,
            start=start,
            target=target,
        )

    def trace(
        self,
        relationships: list[CallRelationship],
        start: str,
        target: str,
    ) -> list[str]:
        return self._search.trace(
            relationships=relationships,
            start=start,
            target=target,
        )

    def trace_route(
        self,
        route_map: dict[str, str],
        relationships: list[CallRelationship],
        route: str,
        target: str,
    ) -> list[str]:
        return self._route_intelligence.trace_route(
            route_map=route_map,
            relationships=relationships,
            route=route,
            target=target,
        )