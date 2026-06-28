# File: cortexfeed/intelligence/intent_classifier.py

from __future__ import annotations

import re

from cortexfeed.intelligence.repository_intent import (
    RepositoryIntent,
)


class IntentClassifier:
    SYMBOL_PATTERNS = [
        r"\bwhere\b",
        r"\bfind\b",
        r"\bhandled\b",
        r"\bimplemented\b",
    ]

    BUG_PATTERNS = [
        r"\berror\b",
        r"\bbug\b",
        r"\bfail\b",
        r"\bexception\b",
        r"\b500\b",
        r"\b404\b",
    ]

    ROUTE_PATTERN = (
        r"\b(GET|POST|PUT|PATCH|DELETE)\s+"
        r"(/[/\w\-]*)"
    )

    def classify(
        self,
        query: str,
    ) -> RepositoryIntent:
        lowered = query.lower()

        routes = [
            f"{m.upper()}:{p}"
            for m, p in re.findall(
                self.ROUTE_PATTERN,
                query,
                re.IGNORECASE,
            )
        ]

        if any(
            re.search(
                pattern,
                lowered,
            )
            for pattern in self.BUG_PATTERNS
        ):
            return RepositoryIntent(
                intent="bug_investigation",
                confidence=0.9,
                routes=routes,
                raw_query=query,
            )

        if any(
            re.search(
                pattern,
                lowered,
            )
            for pattern in self.SYMBOL_PATTERNS
        ):
            return RepositoryIntent(
                intent="symbol_lookup",
                confidence=0.8,
                routes=routes,
                raw_query=query,
            )

        return RepositoryIntent(
            intent="general_search",
            confidence=0.5,
            routes=routes,
            raw_query=query,
        )