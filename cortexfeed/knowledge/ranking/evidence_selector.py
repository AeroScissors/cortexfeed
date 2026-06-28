# File: cortexfeed/knowledge/ranking/evidence_selector.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.graph.graph_search import (
    GraphSearch,
)
from cortexfeed.knowledge.ranking.file_ranker import (
    FileRanker,
)
from cortexfeed.knowledge.ranking.relevance_scorer import (
    RelevanceScorer,
)
from cortexfeed.knowledge.resolver.symbol_resolver import (
    SymbolResolver,
)


@dataclass(slots=True)
class EvidencePackage:
    issue: str

    files: list[dict[str, Any]]
    symbols: list[dict[str, Any]]
    routes: list[dict[str, Any]]
    references: list[dict[str, Any]]

    total_candidates: int


class EvidenceSelector:
    """
    Selects investigation evidence from
    Project Intelligence artifacts.

    Pipeline:

        User Issue
              ↓
        FileRanker
              ↓
        GraphSearch
              ↓
        SymbolResolver
              ↓
        RelevanceScorer
              ↓
        Evidence Package

    Output:

    - relevant files
    - relevant symbols
    - relevant routes
    - relevant references

    Used by:

    - Investigation V3
    - Prompt Builder
    - Context Builder
    - Root Cause Analysis
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

        self.file_ranker = FileRanker(
            project_root=self.project_root,
            graph_path=graph_path,
        )

        self.scorer = (
            RelevanceScorer()
        )

    def select(
        self,
        issue: str,
        *,
        max_files: int = 20,
        max_symbols: int = 25,
        max_routes: int = 10,
        max_references: int = 50,
    ) -> dict[str, Any]:
        ranked_files = (
            self.file_ranker.rank(
                issue,
                limit=max_files,
            )
        )

        graph_nodes = (
            self.graph_search.search(
                issue
            )
        )

        ranked_nodes = (
            self.scorer.score_nodes(
                issue,
                graph_nodes,
            )
        )

        symbols = [
            node
            for node in ranked_nodes
            if node["node_type"]
            in {
                "class",
                "function",
                "method",
            }
        ][:max_symbols]

        routes = [
            node
            for node in ranked_nodes
            if node["node_type"]
            == "route"
        ][:max_routes]

        references = (
            self._collect_references(
                symbols=symbols,
                limit=max_references,
            )
        )

        package = EvidencePackage(
            issue=issue,
            files=ranked_files,
            symbols=symbols,
            routes=routes,
            references=references,
            total_candidates=(
                len(ranked_files)
                + len(symbols)
                + len(routes)
                + len(references)
            ),
        )

        return asdict(package)

    def _collect_references(
        self,
        *,
        symbols: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        results: list[
            dict[str, Any]
        ] = []

        seen: set[str] = set()

        for symbol in symbols:
            symbol_name = symbol[
                "name"
            ]

            references = (
                self.symbol_resolver
                .find_references(
                    symbol_name
                )
            )

            for reference in references:
                key = (
                    f"{reference.file_path}:"
                    f"{reference.line}:"
                    f"{reference.symbol_name}"
                )

                if key in seen:
                    continue

                seen.add(key)

                results.append(
                    {
                        "symbol": (
                            reference
                            .symbol_name
                        ),
                        "file_path": (
                            reference
                            .file_path
                        ),
                        "line": (
                            reference.line
                        ),
                        "context": (
                            reference.context
                        ),
                    }
                )

        results.sort(
            key=lambda item: (
                item["file_path"],
                item["line"],
            )
        )

        return results[:limit]


def select_evidence(
    *,
    project_root: str | Path,
    graph_path: str | Path,
    issue: str,
    max_files: int = 20,
    max_symbols: int = 25,
    max_routes: int = 10,
    max_references: int = 50,
) -> dict[str, Any]:
    selector = EvidenceSelector(
        project_root=project_root,
        graph_path=graph_path,
    )

    return selector.select(
        issue=issue,
        max_files=max_files,
        max_symbols=max_symbols,
        max_routes=max_routes,
        max_references=max_references,
    )