# File: cortexfeed/investigation/planner/question_generator.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import (
    EvidencePlan,
    EvidenceType,
    QuestionBundle,
)


class QuestionStrategy(Protocol):
    def generate(
        self,
        plan: EvidencePlan,
    ) -> QuestionBundle:
        ...


class BaseQuestionStrategy(ABC):
    @abstractmethod
    def generate(
        self,
        plan: EvidencePlan,
    ) -> QuestionBundle:
        raise NotImplementedError


class TemplateQuestionStrategy(BaseQuestionStrategy):
    """
    Deterministic question generator.

    Converts missing evidence into
    concise collection requests.

    Future:
    - conversational variants
    - investigation-specific prompts
    - context-aware grouping
    """

    def generate(
        self,
        plan: EvidencePlan,
    ) -> QuestionBundle:
        if not plan.missing:
            return QuestionBundle(
                questions=[],
                combined_prompt="All required evidence has been collected.",
            )

        questions = [
            self._build_question(
                requirement.evidence_type,
            )
            for requirement in plan.collection_order
        ]

        combined_prompt = self._build_combined_prompt(
            plan,
        )

        return QuestionBundle(
            questions=questions,
            combined_prompt=combined_prompt,
        )

    def _build_question(
        self,
        evidence_type: EvidenceType,
    ) -> str:
        label = self._evidence_label(
            evidence_type,
        )

        return f"Please provide {label}."

    def _build_combined_prompt(
        self,
        plan: EvidencePlan,
    ) -> str:
        lines = [
            "Please provide:",
            "",
        ]

        for index, requirement in enumerate(
            plan.collection_order,
            start=1,
        ):
            lines.append(
                f"{index}. {self._evidence_label(requirement.evidence_type)}"
            )

        return "\n".join(lines)

    def _evidence_label(
        self,
        evidence_type: EvidenceType,
    ) -> str:
        labels = {
            EvidenceType.SERVER_LOGS: "server logs",
            EvidenceType.STACK_TRACE: "stack trace",
            EvidenceType.API_ROUTES: "API routes",
            EvidenceType.REPOSITORY_CODE: "repository implementation",
            EvidenceType.DATABASE_SCHEMA: "database schema",
            EvidenceType.CONFIG_FILE: "configuration files",
            EvidenceType.NETWORK_TRACE: "network trace",
            EvidenceType.TERMINAL_OUTPUT: "terminal output",
            EvidenceType.TEST_RESULTS: "test results",
            EvidenceType.PROJECT_STRUCTURE: "project structure",
        }

        return labels.get(
            evidence_type,
            evidence_type.value.replace("_", " "),
        )


class OllamaQuestionStrategy(BaseQuestionStrategy):
    """
    Future LLM-powered question generation.

    Expected flow:

    EvidencePlan
        ↓
    Prompt Template
        ↓
    Ollama
        ↓
    QuestionBundle
    """

    def generate(
        self,
        plan: EvidencePlan,
    ) -> QuestionBundle:
        raise NotImplementedError(
            "OllamaQuestionStrategy is not implemented yet."
        )


class HybridQuestionStrategy(BaseQuestionStrategy):
    """
    Future orchestration layer.

    Rule-based generation remains
    the deterministic fallback.
    """

    def __init__(
        self,
        fallback_strategy: QuestionStrategy | None = None,
    ) -> None:
        self._fallback_strategy = (
            fallback_strategy
            or TemplateQuestionStrategy()
        )

    def generate(
        self,
        plan: EvidencePlan,
    ) -> QuestionBundle:
        return self._fallback_strategy.generate(
            plan,
        )