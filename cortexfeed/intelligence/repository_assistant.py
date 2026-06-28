# File: cortexfeed/intelligence/repository_assistant.py

from __future__ import annotations

from dataclasses import dataclass, field

from cortexfeed.knowledge.context.models import (
    RepositoryContext,
)


@dataclass(slots=True)
class RepositoryAnswer:
    answer: str
    confidence: float

    symbols: list[str] = field(
        default_factory=list
    )

    routes: list[str] = field(
        default_factory=list
    )

    callers: list[str] = field(
        default_factory=list
    )

    callees: list[str] = field(
        default_factory=list
    )

    call_chains: list[list[str]] = field(
        default_factory=list
    )


class RepositoryAssistant:
    def answer(
        self,
        query: str,
        context: RepositoryContext,
    ) -> RepositoryAnswer:
        query_lower = query.lower()

        #
        # Symbol Lookup
        #

        if (
            "where" in query_lower
            or "handled" in query_lower
            or "implemented" in query_lower
            or "find" in query_lower
        ):
            if context.symbols:
                symbol = context.symbols[0]

                answer = (
                    f"{symbol.name} "
                    f"is present in the repository "
                    f"as a {symbol.node_type.lower()}."
                )

                return RepositoryAnswer(
                    answer=answer,
                    confidence=0.90,
                    symbols=[
                        s.name
                        for s in context.symbols
                    ],
                    routes=context.routes,
                    callers=context.callers,
                    callees=context.callees,
                    call_chains=context.call_chains,
                )

        #
        # Route Lookup
        #

        if context.routes:
            route = context.routes[0]

            answer = (
                f"Route {route} "
                f"was identified and traced through "
                f"the repository graph."
            )

            return RepositoryAnswer(
                answer=answer,
                confidence=0.85,
                symbols=[
                    s.name
                    for s in context.symbols
                ],
                routes=context.routes,
                callers=context.callers,
                callees=context.callees,
                call_chains=context.call_chains,
            )

        #
        # Dependency Lookup
        #

        if context.dependencies:
            dependency = context.dependencies[0]

            answer = (
                f"{dependency.source} "
                f"depends on "
                f"{dependency.target}."
            )

            return RepositoryAnswer(
                answer=answer,
                confidence=0.80,
                symbols=[
                    s.name
                    for s in context.symbols
                ],
                routes=context.routes,
                callers=context.callers,
                callees=context.callees,
                call_chains=context.call_chains,
            )

        #
        # Empty Context
        #

        return RepositoryAnswer(
            answer=(
                "No repository intelligence "
                "was found for the query."
            ),
            confidence=0.0,
            symbols=[],
            routes=[],
            callers=[],
            callees=[],
            call_chains=[],
        )