# File: cortexfeed/knowledge/ranking/relevance_scorer.py

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class RelevanceResult:
    node_id: str
    node_type: str
    name: str
    score: float
    reasons: list[str] = field(
        default_factory=list
    )


class RelevanceScorer:
    """
    Unified relevance scoring engine.

    Scores:

    - files
    - symbols
    - routes
    - graph nodes
    - evidence

    Used by:

    - FileRanker
    - EvidenceSelector
    - Investigation V3
    - Context Builder
    - Prompt Composer
    """

    FILE_MATCH_SCORE = 10.0
    SYMBOL_MATCH_SCORE = 20.0
    ROUTE_MATCH_SCORE = 50.0
    EXACT_MATCH_MULTIPLIER = 2.0
    PARTIAL_MATCH_MULTIPLIER = 1.0

    def score_nodes(
        self,
        query: str,
        nodes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tokens = self._tokenize(query)

        results: list[
            RelevanceResult
        ] = []

        for node in nodes:
            result = self._score_node(
                query=query,
                tokens=tokens,
                node=node,
            )

            if result.score > 0:
                results.append(result)

        ranked = sorted(
            results,
            key=lambda item: (
                -item.score,
                item.name.lower(),
            ),
        )

        return [
            asdict(item)
            for item in ranked
        ]

    def score_node(
        self,
        query: str,
        node: dict[str, Any],
    ) -> dict[str, Any]:
        result = self._score_node(
            query=query,
            tokens=self._tokenize(query),
            node=node,
        )

        return asdict(result)

    def score_evidence(
        self,
        query: str,
        evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tokens = self._tokenize(query)

        results: list[
            RelevanceResult
        ] = []

        for item in evidence:
            content = str(
                item.get("content", "")
            )

            score = 0.0
            reasons: list[str] = []

            for token in tokens:
                occurrences = content.lower().count(
                    token
                )

                if occurrences == 0:
                    continue

                score += (
                    occurrences * 5.0
                )

                reasons.append(
                    f"contains '{token}'"
                )

            if score <= 0:
                continue

            results.append(
                RelevanceResult(
                    node_id=item.get(
                        "id",
                        content[:50],
                    ),
                    node_type=item.get(
                        "type",
                        "evidence",
                    ),
                    name=item.get(
                        "title",
                        "evidence",
                    ),
                    score=score,
                    reasons=reasons,
                )
            )

        results.sort(
            key=lambda item: (
                -item.score,
                item.name.lower(),
            )
        )

        return [
            asdict(item)
            for item in results
        ]

    def _score_node(
        self,
        *,
        query: str,
        tokens: set[str],
        node: dict[str, Any],
    ) -> RelevanceResult:
        score = 0.0
        reasons: list[str] = []

        name = str(
            node.get("name", "")
        )

        node_type = str(
            node.get("node_type", "")
        )

        normalized_name = (
            name.replace("_", " ")
            .replace("-", " ")
            .lower()
        )

        query_lower = query.lower()

        if normalized_name == query_lower:
            score += (
                self.SYMBOL_MATCH_SCORE
                * self.EXACT_MATCH_MULTIPLIER
            )

            reasons.append(
                "exact match"
            )

        elif query_lower in normalized_name:
            score += (
                self.SYMBOL_MATCH_SCORE
                * self.PARTIAL_MATCH_MULTIPLIER
            )

            reasons.append(
                "partial query match"
            )

        for token in tokens:
            if len(token) < 3:
                continue

            if token not in normalized_name:
                continue

            if node_type == "file":
                score += (
                    self.FILE_MATCH_SCORE
                )

                reasons.append(
                    f"filename contains '{token}'"
                )

            elif node_type in {
                "class",
                "function",
                "method",
            }:
                score += (
                    self.SYMBOL_MATCH_SCORE
                )

                reasons.append(
                    f"symbol contains '{token}'"
                )

            elif node_type == "route":
                score += (
                    self.ROUTE_MATCH_SCORE
                )

                reasons.append(
                    f"route contains '{token}'"
                )

            else:
                score += 5.0

                reasons.append(
                    f"contains '{token}'"
                )

        metadata = node.get(
            "metadata",
            {},
        )

        if isinstance(metadata, dict):
            metadata_text = (
                " ".join(
                    str(value)
                    for value in metadata.values()
                )
                .lower()
            )

            for token in tokens:
                if token in metadata_text:
                    score += 3.0

                    reasons.append(
                        f"metadata contains '{token}'"
                    )

        return RelevanceResult(
            node_id=str(
                node.get("id", "")
            ),
            node_type=node_type,
            name=name,
            score=score,
            reasons=list(
                dict.fromkeys(reasons)
            ),
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


def score_nodes(
    query: str,
    nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scorer = RelevanceScorer()

    return scorer.score_nodes(
        query=query,
        nodes=nodes,
    )


def score_evidence(
    query: str,
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scorer = RelevanceScorer()

    return scorer.score_evidence(
        query=query,
        evidence=evidence,
    )