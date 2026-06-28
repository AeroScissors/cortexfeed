# File: cortexfeed/knowledge/graph/v3/graph_storage_v3.py

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import KnowledgeGraphV3


class GraphStorageV3:
    def save(
        self,
        graph: KnowledgeGraphV3,
        output_path: Path,
    ) -> None:
        payload = {
            "nodes": {
                key: asdict(value)
                for key, value in graph.nodes.items()
            },
            "edges": [
                asdict(edge)
                for edge in graph.edges
            ],
        }

        output_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )