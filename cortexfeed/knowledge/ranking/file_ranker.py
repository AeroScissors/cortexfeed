# File: cortexfeed/knowledge/ranking/file_ranker.py

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.graph.graph_search import (
    GraphSearch,
)
from cortexfeed.knowledge.resolver.symbol_resolver import (
    SymbolResolver,
)


@dataclass(slots=True)
class RankedFile:
    file_path: str
    score: float
    reasons: list[str] = field(
        default_factory=list
    )


class FileRanker:
    """
    Ranks repository files by relevance to a user issue.

    Signals:

    - filename matches
    - symbol matches
    - route matches
    - dependency proximity
    - reference proximity

    Used by:

    - Investigation V3
    - Context Selection
    - Prompt Building
    - Evidence Collection
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

    def rank(
        self,
        issue: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        tokens = self._tokenize(issue)

        scores: dict[str, RankedFile] = {}

        self._score_filename_matches(
            tokens,
            scores,
        )

        self._score_symbol_matches(
            tokens,
            scores,
        )

        self._score_route_matches(
            issue,
            scores,
        )

        self._score_dependency_matches(
            scores,
        )

        ranked = sorted(
            scores.values(),
            key=lambda item: (
                -item.score,
                item.file_path,
            ),
        )

        return [
            asdict(item)
            for item in ranked[:limit]
        ]

    def _score_filename_matches(
        self,
        tokens: set[str],
        scores: dict[str, RankedFile],
    ) -> None:
        for node in self.graph_search.nodes:
            if node["node_type"] != "file":
                continue

            file_name = node["name"].lower()

            for token in tokens:
                if len(token) < 3:
                    continue

                if token in file_name:
                    self._add_score(
                        scores=scores,
                        file_path=node["id"],
                        score=10.0,
                        reason=(
                            f"filename matches "
                            f"'{token}'"
                        ),
                    )

    def _score_symbol_matches(
        self,
        tokens: set[str],
        scores: dict[str, RankedFile],
    ) -> None:
        index = self.symbol_resolver.build()

        for symbol in index["symbols"]:
            definition = symbol[
                "definition"
            ]

            symbol_name = (
                definition["name"]
                .replace("_", " ")
                .lower()
            )

            for token in tokens:
                if len(token) < 3:
                    continue

                if token in symbol_name:
                    self._add_score(
                        scores=scores,
                        file_path=definition[
                            "file_path"
                        ],
                        score=20.0,
                        reason=(
                            f"symbol matches "
                            f"'{token}'"
                        ),
                    )

    def _score_route_matches(
        self,
        issue: str,
        scores: dict[str, RankedFile],
    ) -> None:
        routes = re.findall(
            r"/[a-zA-Z0-9_\-/]+",
            issue,
        )

        if not routes:
            return

        for route in routes:
            matches = (
                self.graph_search.find_route(
                    route
                )
            )

            for match in matches:
                node_id = match["id"]

                file_path = (
                    node_id.split("::")[0]
                )

                self._add_score(
                    scores=scores,
                    file_path=file_path,
                    score=50.0,
                    reason=(
                        f"route match "
                        f"'{route}'"
                    ),
                )

    def _score_dependency_matches(
        self,
        scores: dict[str, RankedFile],
    ) -> None:
        current_files = list(
            scores.keys()
        )

        for file_path in current_files:
            dependencies = (
                self.graph_search
                .find_dependencies(
                    file_path
                )
            )

            for dependency in (
                dependencies
            ):
                self._add_score(
                    scores=scores,
                    file_path=dependency[
                        "target"
                    ],
                    score=5.0,
                    reason=(
                        "imported by "
                        f"{file_path}"
                    ),
                )

    def _add_score(
        self,
        *,
        scores: dict[str, RankedFile],
        file_path: str,
        score: float,
        reason: str,
    ) -> None:
        if file_path not in scores:
            scores[file_path] = (
                RankedFile(
                    file_path=file_path,
                )
            )

        scores[file_path].score += score

        if (
            reason
            not in scores[
                file_path
            ].reasons
        ):
            scores[
                file_path
            ].reasons.append(
                reason
            )

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:
        return {
            token.lower()
            for token in re.findall(
                r"[a-zA-Z_][a-zA-Z0-9_]*",
                text,
            )
        }


def rank_files(
    *,
    project_root: str | Path,
    graph_path: str | Path,
    issue: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    ranker = FileRanker(
        project_root=project_root,
        graph_path=graph_path,
    )

    return ranker.rank(
        issue,
        limit=limit,
    )