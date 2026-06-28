# File: cortexfeed/intelligence/query_router.py

from __future__ import annotations

import re

from cortexfeed.intelligence.capabilities.registry import (
    CapabilityRegistry,
)
from cortexfeed.intelligence.capabilities.models import (
    CapabilityResult,
)


class QueryRouter:
    ROUTE_PATTERN = (
        r"\b(GET|POST|PUT|PATCH|DELETE)\s+"
        r"(/[/\w\-]*)"
    )

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
    ) -> None:
        self.capability_registry = (
            capability_registry
        )

    def _clean_symbol(
        self,
        query: str,
        noise_words: list[str],
    ) -> str:
        symbol = query

        for word in noise_words:
            symbol = re.sub(
                rf"\b{re.escape(word)}\b",
                "",
                symbol,
                flags=re.IGNORECASE,
            )

        symbol = symbol.replace("?", "")

        return symbol.strip()

    def route(
        self,
        query: str,
    ) -> CapabilityResult:
        query = query.strip()

        if not query:
            return CapabilityResult(
                capability="none",
                confidence=0.0,
                summary="Empty query.",
            )

        lowered = query.lower()

        #
        # Route Trace
        #

        route_match = re.search(
            self.ROUTE_PATTERN,
            query,
            re.IGNORECASE,
        )

        if (
            route_match
            and any(
                keyword in lowered
                for keyword in [
                    "trace",
                    "flow",
                    "path",
                    "route",
                ]
            )
        ):
            method = route_match.group(1)
            path = route_match.group(2)

            capability = (
                self.capability_registry.get(
                    "route_trace",
                )
            )

            return capability.execute(
                method,
                path,
            )

        #
        # Impact Analysis
        #

        impact_patterns = [
            "what breaks if",
            "impact",
            "affected by",
            "depends on",
            "blast radius",
        ]

        for pattern in impact_patterns:
            if pattern in lowered:
                symbol = self._clean_symbol(
                    query,
                    [
                        "what breaks if",
                        "impact",
                        "affected by",
                        "depends on",
                        "blast radius",
                        "changes",
                        "change",
                        "for",
                        "the",
                        "of",
                    ],
                )

                capability = (
                    self.capability_registry.get(
                        "impact_analysis",
                    )
                )

                return capability.execute(
                    symbol,
                )

        #
        # Who Calls (callers lookup)
        #

        who_calls_patterns = [
            "who calls",
            "what calls",
            "callers of",
            "called by",
        ]

        for pattern in who_calls_patterns:
            if pattern in lowered:
                symbol = self._clean_symbol(
                    query,
                    [
                        "who calls",
                        "what calls",
                        "callers of",
                        "called by",
                        "who",
                        "what",
                        "calls",
                        "the",
                    ],
                )

                capability = (
                    self.capability_registry.get(
                        "where_is_symbol",
                    )
                )

                return capability.execute(symbol)

        #
        # What Does X Call (callees lookup)
        #

        what_calls_patterns = [
            "what does",
            "callees of",
            "calls from",
            "what is called by",
        ]

        for pattern in what_calls_patterns:
            if pattern in lowered:
                symbol = self._clean_symbol(
                    query,
                    [
                        "what does",
                        "callees of",
                        "calls from",
                        "what is called by",
                        "what",
                        "does",
                        "call",
                        "calls",
                        "the",
                    ],
                )

                capability = (
                    self.capability_registry.get(
                        "where_is_symbol",
                    )
                )

                return capability.execute(symbol)

        #
        # Call Chain
        #

        call_chain_patterns = [
            "execution flow",
            "execution path",
            "call chain",
            "flow",
        ]

        for pattern in call_chain_patterns:
            if pattern in lowered:
                symbol = self._clean_symbol(
                    query,
                    [
                        "show",
                        "trace",
                        "execution flow",
                        "execution path",
                        "call chain",
                        "flow",
                        "for",
                        "the",
                    ],
                )

                capability = (
                    self.capability_registry.get(
                        "call_chain",
                    )
                )

                return capability.execute(
                    symbol,
                )

        #
        # Symbol Lookup
        #

        symbol_patterns = [
            "where is",
            "where",
            "find",
            "implemented",
            "handled",
            "defined",
        ]

        for pattern in symbol_patterns:
            if pattern in lowered:
                symbol = self._clean_symbol(
                    query,
                    [
                        "where is",
                        "where",
                        "find",
                        "handled",
                        "implemented",
                        "defined",
                        "located",
                        "declared",
                        "for",
                        "the",
                    ],
                )

                capability = (
                    self.capability_registry.get(
                        "where_is_symbol",
                    )
                )

                return capability.execute(
                    symbol,
                )

        return CapabilityResult(
            capability="unknown",
            confidence=0.0,
            summary=(
                "No capability matched the query."
            ),
        )