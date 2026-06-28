# File: cortexfeed/knowledge/graph/v3/query_parser.py

from __future__ import annotations

import re

from cortexfeed.knowledge.graph.v3.query_models import (
    QueryIntent,
)


class QueryParser:
    """
    Converts repository questions into structured intents.

    Supported:

    Who calls X?

    What does X call?

    Can A reach B?

    Trace A -> B
    """

    WHO_CALLS_PATTERN = re.compile(
        r"who\s+calls\s+(.+?)\??$",
        re.IGNORECASE,
    )

    WHAT_CALLS_PATTERN = re.compile(
        r"what\s+does\s+(.+?)\s+call\??$",
        re.IGNORECASE,
    )

    CAN_REACH_PATTERN = re.compile(
        r"can\s+(.+?)\s+reach\s+(.+?)\??$",
        re.IGNORECASE,
    )

    TRACE_PATTERN = re.compile(
        r"trace\s+(.+?)\s*->\s*(.+?)$",
        re.IGNORECASE,
    )

    def parse(
        self,
        query: str,
    ) -> QueryIntent:
        query = query.strip()

        match = self.WHO_CALLS_PATTERN.match(
            query,
        )

        if match:
            return QueryIntent(
                intent_type="who_calls",
                symbol=match.group(1).strip(),
                raw_query=query,
            )

        match = self.WHAT_CALLS_PATTERN.match(
            query,
        )

        if match:
            return QueryIntent(
                intent_type="what_does_call",
                symbol=match.group(1).strip(),
                raw_query=query,
            )

        match = self.CAN_REACH_PATTERN.match(
            query,
        )

        if match:
            return QueryIntent(
                intent_type="can_reach",
                start=match.group(1).strip(),
                target=match.group(2).strip(),
                raw_query=query,
            )

        match = self.TRACE_PATTERN.match(
            query,
        )

        if match:
            return QueryIntent(
                intent_type="trace",
                start=match.group(1).strip(),
                target=match.group(2).strip(),
                raw_query=query,
            )

        return QueryIntent(
            intent_type="unknown",
            raw_query=query,
        )