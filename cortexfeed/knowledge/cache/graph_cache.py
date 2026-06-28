# File: cortexfeed/knowledge/cache/graph_cache.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CachedGraphIndexes:
    nodes_by_id: dict[str, dict[str, Any]]
    nodes_by_type: dict[str, list[dict[str, Any]]]
    nodes_by_name: dict[str, list[dict[str, Any]]]
    outgoing_edges: dict[str, list[dict[str, Any]]]
    incoming_edges: dict[str, list[dict[str, Any]]]


class GraphCache:
    """
    In-memory graph acceleration layer.

    Purpose:

    - O(1) node lookup
    - Fast symbol lookup
    - Fast route lookup
    - Fast dependency traversal
    - Fast investigation ranking

    Consumed by:

    - GraphSearch
    - FileRanker
    - EvidenceSelector
    - Investigation V3
    """

    def __init__(
        self,
    ) -> None:
        self._cache: dict[
            str,
            CachedGraphIndexes
        ] = {}

    def load_graph(
        self,
        graph_file: str | Path,
    ) -> CachedGraphIndexes:
        graph_file = str(
            Path(graph_file).resolve()
        )

        if graph_file in self._cache:
            return self._cache[
                graph_file
            ]

        with open(
            graph_file,
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(
                handle
            )

        graph = payload.get(
            "graph",
            payload,
        )

        indexes = self._build_indexes(
            graph
        )

        self._cache[
            graph_file
        ] = indexes

        return indexes

    def invalidate(
        self,
        graph_file: str | Path,
    ) -> None:
        graph_file = str(
            Path(graph_file).resolve()
        )

        self._cache.pop(
            graph_file,
            None,
        )

    def clear(
        self,
    ) -> None:
        self._cache.clear()

    def contains(
        self,
        graph_file: str | Path,
    ) -> bool:
        graph_file = str(
            Path(graph_file).resolve()
        )

        return (
            graph_file
            in self._cache
        )

    def get_node(
        self,
        graph_file: str | Path,
        node_id: str,
    ) -> dict[str, Any] | None:
        indexes = self.load_graph(
            graph_file
        )

        return indexes.nodes_by_id.get(
            node_id
        )

    def find_by_name(
        self,
        graph_file: str | Path,
        name: str,
    ) -> list[dict[str, Any]]:
        indexes = self.load_graph(
            graph_file
        )

        return indexes.nodes_by_name.get(
            name.lower(),
            [],
        )

    def find_by_type(
        self,
        graph_file: str | Path,
        node_type: str,
    ) -> list[dict[str, Any]]:
        indexes = self.load_graph(
            graph_file
        )

        return indexes.nodes_by_type.get(
            node_type,
            [],
        )

    def outgoing(
        self,
        graph_file: str | Path,
        node_id: str,
    ) -> list[dict[str, Any]]:
        indexes = self.load_graph(
            graph_file
        )

        return indexes.outgoing_edges.get(
            node_id,
            [],
        )

    def incoming(
        self,
        graph_file: str | Path,
        node_id: str,
    ) -> list[dict[str, Any]]:
        indexes = self.load_graph(
            graph_file
        )

        return indexes.incoming_edges.get(
            node_id,
            [],
        )

    def _build_indexes(
        self,
        graph: dict[str, Any],
    ) -> CachedGraphIndexes:
        nodes_by_id: dict[
            str,
            dict[str, Any]
        ] = {}

        nodes_by_type: dict[
            str,
            list[dict[str, Any]]
        ] = {}

        nodes_by_name: dict[
            str,
            list[dict[str, Any]]
        ] = {}

        outgoing_edges: dict[
            str,
            list[dict[str, Any]]
        ] = {}

        incoming_edges: dict[
            str,
            list[dict[str, Any]]
        ] = {}

        for node in graph.get(
            "nodes",
            [],
        ):
            node_id = node["id"]

            nodes_by_id[node_id] = node

            node_type = node[
                "node_type"
            ]

            nodes_by_type.setdefault(
                node_type,
                [],
            ).append(node)

            node_name = (
                node["name"]
                .lower()
                .strip()
            )

            nodes_by_name.setdefault(
                node_name,
                [],
            ).append(node)

        for edge in graph.get(
            "edges",
            [],
        ):
            source = edge["source"]
            target = edge["target"]

            outgoing_edges.setdefault(
                source,
                [],
            ).append(edge)

            incoming_edges.setdefault(
                target,
                [],
            ).append(edge)

        return CachedGraphIndexes(
            nodes_by_id=nodes_by_id,
            nodes_by_type=nodes_by_type,
            nodes_by_name=nodes_by_name,
            outgoing_edges=outgoing_edges,
            incoming_edges=incoming_edges,
        )


_graph_cache = GraphCache()


def load_graph_cache(
    graph_file: str | Path,
) -> CachedGraphIndexes:
    return _graph_cache.load_graph(
        graph_file
    )


def invalidate_graph_cache(
    graph_file: str | Path,
) -> None:
    _graph_cache.invalidate(
        graph_file
    )


def clear_graph_cache() -> None:
    _graph_cache.clear()