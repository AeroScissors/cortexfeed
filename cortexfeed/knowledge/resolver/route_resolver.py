# File: cortexfeed/knowledge/resolver/route_resolver.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.graph.graph_search import (
    GraphSearch,
)
from cortexfeed.knowledge.resolver.symbol_resolver import (
    SymbolResolver,
)


@dataclass(slots=True)
class RouteMatch:
    route_path: str
    method: str
    file_path: str
    node_id: str


class RouteResolver:
    """
    Route intelligence layer.

    Answers:

    - Where is route X defined?
    - Which handler serves route X?
    - Which file owns route X?
    - What symbols exist in the route file?
    - What references exist around the route?

    Used by:

    - Investigation V3
    - API debugging
    - Backend tracing
    - Context selection
    """

    def __init__(
        self,
        project_root: str | Path,
        graph_path: str | Path,
    ) -> None:
        self.project_root = Path(
            project_root
        ).resolve()

        self.graph_search = GraphSearch(
            graph_path
        )

        self.symbol_resolver = (
            SymbolResolver(
                self.project_root
            )
        )

    def find_route(
        self,
        route_path: str,
    ) -> list[dict[str, Any]]:
        matches = (
            self.graph_search.find_route(
                route_path
            )
        )

        results: list[
            dict[str, Any]
        ] = []

        for route in matches:
            metadata = route.get(
                "metadata",
                {},
            )

            node_id = route["id"]

            file_path = (
                node_id.split("::")[0]
            )

            results.append(
                asdict(
                    RouteMatch(
                        route_path=metadata.get(
                            "path",
                            route_path,
                        ),
                        method=metadata.get(
                            "method",
                            "UNKNOWN",
                        ),
                        file_path=file_path,
                        node_id=node_id,
                    )
                )
            )

        return results

    def find_handler(
        self,
        route_path: str,
    ) -> dict[str, Any] | None:
        routes = self.find_route(
            route_path
        )

        if not routes:
            return None

        route = routes[0]

        route_node = (
            self.graph_search.get_node(
                route["node_id"]
            )
        )

        if route_node is None:
            return None

        metadata = route_node.get(
            "metadata",
            {},
        )

        return {
            "route": route_path,
            "method": metadata.get(
                "method"
            ),
            "handler": metadata.get(
                "function_name"
            ),
            "file_path": route[
                "file_path"
            ],
        }

    def route_symbols(
        self,
        route_path: str,
    ) -> list[dict[str, Any]]:
        handler = self.find_handler(
            route_path
        )

        if handler is None:
            return []

        file_path = handler[
            "file_path"
        ]

        index = (
            self.symbol_resolver.build()
        )

        symbols: list[
            dict[str, Any]
        ] = []

        for symbol in index[
            "symbols"
        ]:
            definition = symbol[
                "definition"
            ]

            if (
                definition[
                    "file_path"
                ]
                != file_path
            ):
                continue

            symbols.append(
                definition
            )

        return symbols

    def route_references(
        self,
        route_path: str,
    ) -> list[dict[str, Any]]:
        handler = self.find_handler(
            route_path
        )

        if handler is None:
            return []

        function_name = handler[
            "handler"
        ]

        references = (
            self.symbol_resolver
            .find_references(
                function_name
            )
        )

        return [
            {
                "symbol": (
                    reference.symbol_name
                ),
                "file_path": (
                    reference.file_path
                ),
                "line": (
                    reference.line
                ),
                "context": (
                    reference.context
                ),
            }
            for reference in references
        ]

    def route_context(
        self,
        route_path: str,
    ) -> dict[str, Any]:
        handler = self.find_handler(
            route_path
        )

        return {
            "handler": handler,
            "symbols": (
                self.route_symbols(
                    route_path
                )
            ),
            "references": (
                self.route_references(
                    route_path
                )
            ),
        }

    def all_routes(
        self,
    ) -> list[dict[str, Any]]:
        routes = []

        for node in (
            self.graph_search.nodes
        ):
            if (
                node["node_type"]
                != "route"
            ):
                continue

            metadata = node.get(
                "metadata",
                {},
            )

            routes.append(
                {
                    "path": metadata.get(
                        "path"
                    ),
                    "method": metadata.get(
                        "method"
                    ),
                    "handler": metadata.get(
                        "function_name"
                    ),
                }
            )

        routes.sort(
            key=lambda item: (
                item["path"] or ""
            )
        )

        return routes

    def request_trace(
        self,
        route_path: str,
    ) -> dict[str, Any]:
        """
        First-generation request tracing.

        Current implementation:

        Route
            ->
        Handler
            ->
        References

        Future versions can extend
        this with service and repository
        traversal.
        """

        handler = self.find_handler(
            route_path
        )

        if handler is None:
            return {
                "route": route_path,
                "trace": [],
            }

        trace = [
            {
                "type": "route",
                "value": route_path,
            },
            {
                "type": "handler",
                "value": handler[
                    "handler"
                ],
            },
        ]

        references = (
            self.route_references(
                route_path
            )
        )

        for reference in references:
            trace.append(
                {
                    "type": "reference",
                    "value": (
                        reference[
                            "symbol"
                        ]
                    ),
                    "file_path": (
                        reference[
                            "file_path"
                        ]
                    ),
                }
            )

        return {
            "route": route_path,
            "trace": trace,
        }


def create_route_resolver(
    project_root: str | Path,
    graph_path: str | Path,
) -> RouteResolver:
    return RouteResolver(
        project_root=project_root,
        graph_path=graph_path,
    )