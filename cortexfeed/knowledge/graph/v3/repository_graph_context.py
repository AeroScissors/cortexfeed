# File: cortexfeed/knowledge/graph/v3/repository_graph_context.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cortexfeed.knowledge.graph.v3.models import (
    KnowledgeGraphV3,
)


@dataclass(slots=True)
class RepositoryGraphContext:
    """
    Shared repository intelligence context.

    Contains all artifacts required for
    graph search, route tracing, and
    investigation intelligence.
    """

    graph: KnowledgeGraphV3

    symbols: dict[str, Any]

    routes: dict[str, Any]

    project_tree: dict[str, Any]