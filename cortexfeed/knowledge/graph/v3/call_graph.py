# File: cortexfeed/knowledge/graph/v3/call_graph.py

from __future__ import annotations

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.models import (
    EdgeType,
    GraphEdge,
)


class CallGraphBuilder:
    """
    Converts resolved call relationships into graph edges.

    Example:

    Controller.login
        ↓
    AuthService.login

    becomes

    Controller.login
        CALLS
    AuthService.login
    """

    def build(
        self,
        relationships: list[CallRelationship],
    ) -> list[GraphEdge]:
        edges: list[GraphEdge] = []

        for relationship in relationships:
            edges.append(
                GraphEdge(
                    source=relationship.caller_symbol,
                    target=relationship.callee_symbol,
                    edge_type=EdgeType.CALLS,
                )
            )

        return edges