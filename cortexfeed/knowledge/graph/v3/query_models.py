# File: cortexfeed/knowledge/graph/v3/query_models.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class QueryIntent:
    """
    Parsed repository intelligence query.
    """

    intent_type: str

    symbol: str | None = None

    start: str | None = None

    target: str | None = None

    raw_query: str = ""