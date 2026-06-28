# File: cortexfeed/knowledge/retrieval/semantic_retriever.py

from __future__ import annotations

from cortexfeed.intelligence.repository_intent import (
    RepositoryIntent,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)


class SemanticRetriever:
    def __init__(
        self,
        graph_search: GraphSearchV2,
    ) -> None:
        self.graph_search = graph_search

    def retrieve(
        self,
        intent: RepositoryIntent,
    ) -> dict:
        results = {
            "symbols": [],
            "routes": [],
            "files": [],
        }

        #
        # Route Retrieval
        #

        for route in intent.routes:
            if ":" not in route:
                continue

            method, path = route.split(
                ":",
                1,
            )

            route_nodes = (
                self.graph_search.route_trace(
                    method,
                    path,
                )
            )

            results["routes"].append(
                route,
            )

            results["symbols"].extend(
                node.name
                for node in route_nodes
            )

        #
        # Symbol Retrieval
        #

        for token in intent.raw_query.split():
            node = self.graph_search.find_node(
                token,
            )

            if node:
                results["symbols"].append(
                    node.name,
                )

        results["symbols"] = sorted(
            set(results["symbols"])
        )

        results["routes"] = sorted(
            set(results["routes"])
        )

        results["files"] = sorted(
            set(results["files"])
        )

        return results