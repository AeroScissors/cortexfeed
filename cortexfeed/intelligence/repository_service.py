# File: cortexfeed/intelligence/repository_service.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cortexfeed.intelligence.query_router import (
    QueryRouter,
)
from cortexfeed.intelligence.capabilities.models import (
    CapabilityResult,
)


@dataclass(slots=True)
class RepositoryAnswer:
    answer: str
    confidence: float
    capability: str

    evidence: list[str] = field(
        default_factory=list,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


class RepositoryService:
    def __init__(
        self,
        query_router: QueryRouter,
    ) -> None:
        self.query_router = query_router

    def answer(
        self,
        query: str,
    ) -> RepositoryAnswer:
        result = self.query_router.route(
            query,
        )

        answer = self._build_answer(
            result,
        )

        evidence = self._extract_evidence(
            result,
        )

        return RepositoryAnswer(
            answer=answer,
            confidence=result.confidence,
            capability=result.capability,
            evidence=evidence,
            metadata=dict(
                result.metadata,
            ),
        )

    def _build_answer(
        self,
        result: CapabilityResult,
    ) -> str:
        if result.capability == "none":
            return "Empty query."

        if result.capability == "unknown":
            return (
                "Unable to determine the repository "
                "question being asked."
            )

        if result.capability == "where_is_symbol":
            lines = [
                result.summary,
            ]

            if result.callers:
                lines.append("")
                lines.append("Called by:")

                for caller in result.callers:
                    lines.append(
                        f"- {caller}"
                    )

            if result.callees:
                lines.append("")
                lines.append("Calls:")

                for callee in result.callees:
                    lines.append(
                        f"- {callee}"
                    )

            return "\n".join(
                lines,
            )

        if result.capability == "route_trace":
            lines = [
                result.summary,
            ]

            if result.execution_path:
                lines.append("")
                lines.append(
                    "Execution Path:"
                )

                for symbol in result.execution_path:
                    lines.append(
                        f"- {symbol}"
                    )

            return "\n".join(
                lines,
            )

        if result.capability == "impact_analysis":
            lines = [
                result.summary,
            ]

            dependents = (
                result.metadata.get(
                    "dependents",
                    [],
                )
            )

            if dependents:
                lines.append("")
                lines.append(
                    "Dependents:"
                )

                for dependent in dependents:
                    lines.append(
                        f"- {dependent}"
                    )

            return "\n".join(
                lines,
            )

        if result.capability == "call_chain":
            lines = [
                result.summary,
            ]

            if result.execution_path:
                lines.append("")
                lines.append(
                    "Call Chain:"
                )

                for symbol in result.execution_path:
                    lines.append(
                        f"- {symbol}"
                    )

            return "\n".join(
                lines,
            )

        return result.summary

    def _extract_evidence(
        self,
        result: CapabilityResult,
    ) -> list[str]:
        evidence: list[str] = []

        evidence.extend(
            result.symbols,
        )

        evidence.extend(
            result.routes,
        )

        evidence.extend(
            result.callers,
        )

        evidence.extend(
            result.callees,
        )

        evidence.extend(
            result.execution_path,
        )

        return sorted(
            set(evidence),
        )