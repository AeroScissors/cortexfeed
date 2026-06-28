# File: cortexfeed/knowledge/graph/graph_storage.py

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GRAPH_SCHEMA_VERSION = "1.0"


@dataclass(slots=True)
class GraphMetadata:
    project_name: str
    schema_version: str
    created_at: str
    node_count: int
    edge_count: int


class GraphStorage:
    """
    Persistent graph storage layer.

    Responsibilities:

    - Save graph.json
    - Load graph.json
    - Validate graph structure
    - Manage schema versions
    - Support future migrations

    Storage Format:

    {
        "metadata": {...},
        "graph": {...}
    }
    """

    def __init__(
        self,
        graph_file: str | Path,
    ) -> None:
        self.graph_file = Path(graph_file)

    def save(
        self,
        graph: dict[str, Any],
    ) -> Path:
        self.graph_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        metadata = GraphMetadata(
            project_name=graph["project"],
            schema_version=GRAPH_SCHEMA_VERSION,
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            node_count=graph["node_count"],
            edge_count=graph["edge_count"],
        )

        payload = {
            "metadata": asdict(metadata),
            "graph": graph,
        }

        with self.graph_file.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                ensure_ascii=False,
            )

        return self.graph_file

    def load(
        self,
    ) -> dict[str, Any]:
        if not self.graph_file.exists():
            raise FileNotFoundError(
                f"Graph not found: {self.graph_file}"
            )

        with self.graph_file.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        self.validate(payload)

        return payload["graph"]

    def load_with_metadata(
        self,
    ) -> dict[str, Any]:
        if not self.graph_file.exists():
            raise FileNotFoundError(
                f"Graph not found: {self.graph_file}"
            )

        with self.graph_file.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        self.validate(payload)

        return payload

    def validate(
        self,
        payload: dict[str, Any],
    ) -> None:
        if "metadata" not in payload:
            raise ValueError(
                "Missing graph metadata"
            )

        if "graph" not in payload:
            raise ValueError(
                "Missing graph data"
            )

        metadata = payload["metadata"]
        graph = payload["graph"]

        required_metadata = {
            "project_name",
            "schema_version",
            "created_at",
            "node_count",
            "edge_count",
        }

        missing_metadata = (
            required_metadata
            - set(metadata.keys())
        )

        if missing_metadata:
            raise ValueError(
                f"Missing metadata fields: "
                f"{sorted(missing_metadata)}"
            )

        required_graph = {
            "project",
            "nodes",
            "edges",
            "node_count",
            "edge_count",
        }

        missing_graph = (
            required_graph
            - set(graph.keys())
        )

        if missing_graph:
            raise ValueError(
                f"Missing graph fields: "
                f"{sorted(missing_graph)}"
            )

    def exists(
        self,
    ) -> bool:
        return self.graph_file.exists()

    def delete(
        self,
    ) -> bool:
        if not self.graph_file.exists():
            return False

        self.graph_file.unlink()

        return True

    def schema_version(
        self,
    ) -> str:
        payload = self.load_with_metadata()

        return payload["metadata"][
            "schema_version"
        ]


def save_graph(
    graph: dict[str, Any],
    graph_file: str | Path,
) -> Path:
    storage = GraphStorage(graph_file)

    return storage.save(graph)


def load_graph(
    graph_file: str | Path,
) -> dict[str, Any]:
    storage = GraphStorage(graph_file)

    return storage.load()