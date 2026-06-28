# File: cortexfeed/knowledge/graph/v3/execution_search.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.execution_trace import (
    ExecutionTraceBuilder,
)


class ExecutionSearch:
    """
    Query interface for execution relationships.

    Examples:

    Who calls AuthService.login?

    What does Controller.login call?

    Trace execution into UserRepository.find_user?
    """

    def __init__(self) -> None:
        self._trace_builder = ExecutionTraceBuilder()

    def find_callers(
        self,
        relationships: list[CallRelationship],
        symbol: str,
    ) -> list[str]:
        callers: list[str] = []

        for relationship in relationships:
            if relationship.callee_symbol == symbol:
                callers.append(
                    relationship.caller_symbol,
                )

        return sorted(set(callers))

    def find_callees(
        self,
        relationships: list[CallRelationship],
        symbol: str,
    ) -> list[str]:
        callees: list[str] = []

        for relationship in relationships:
            if relationship.caller_symbol == symbol:
                callees.append(
                    relationship.callee_symbol,
                )

        return sorted(set(callees))

    def trace(
        self,
        relationships: list[CallRelationship],
        start: str,
        target: str,
    ) -> list[str]:
        return self._trace_builder.trace(
            relationships=relationships,
            start=start,
            target=target,
        )

    def has_path(
        self,
        relationships: list[CallRelationship],
        start: str,
        target: str,
    ) -> bool:
        path = self.trace(
            relationships=relationships,
            start=start,
            target=target,
        )

        return len(path) > 0