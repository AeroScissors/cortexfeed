# File: cortexfeed/investigation/planner/intent_analyzer.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import (
    InvestigationDomain,
    InvestigationIntent,
    InvestigationType,
)


class IntentClassifier(Protocol):
    def classify(
        self,
        request: str,
    ) -> InvestigationIntent:
        ...


class BaseIntentClassifier(ABC):
    @abstractmethod
    def classify(
        self,
        request: str,
    ) -> InvestigationIntent:
        raise NotImplementedError


class RuleBasedIntentClassifier(BaseIntentClassifier):
    """
    Deterministic classifier.

    Phase 1:
    - keyword matching
    - lightweight confidence scoring

    Future:
    - HybridIntentClassifier
    - OllamaIntentClassifier
    """

    def classify(
        self,
        request: str,
    ) -> InvestigationIntent:
        normalized = request.strip().lower()

        investigation_type, type_confidence = self._detect_type(
            normalized,
        )

        domain, domain_confidence = self._detect_domain(
            normalized,
        )

        confidence = round(
            (type_confidence + domain_confidence) / 2,
            2,
        )

        return InvestigationIntent(
            raw_request=request,
            investigation_type=investigation_type,
            domain=domain,
            confidence=confidence,
        )

    def _detect_type(
        self,
        text: str,
    ) -> tuple[InvestigationType, float]:
        rules: list[
            tuple[
                InvestigationType,
                tuple[str, ...],
                float,
            ]
        ] = [
            (
                InvestigationType.DEBUGGING,
                (
                    "fix",
                    "bug",
                    "error",
                    "broken",
                    "not working",
                    "issue",
                    "sync",
                    "failing",
                ),
                0.95,
            ),
            (
                InvestigationType.ROOT_CAUSE,
                (
                    "why",
                    "root cause",
                    "cause",
                    "reason",
                ),
                0.90,
            ),
            (
                InvestigationType.PERFORMANCE,
                (
                    "slow",
                    "latency",
                    "performance",
                    "memory",
                    "cpu",
                ),
                0.90,
            ),
            (
                InvestigationType.SECURITY,
                (
                    "security",
                    "auth bypass",
                    "token",
                    "jwt",
                    "vulnerability",
                ),
                0.90,
            ),
            (
                InvestigationType.TEST_FAILURE,
                (
                    "test",
                    "failing test",
                    "unit test",
                    "integration test",
                ),
                0.90,
            ),
            (
                InvestigationType.ARCHITECTURE_REVIEW,
                (
                    "architecture",
                    "design",
                    "review",
                    "structure",
                ),
                0.85,
            ),
            (
                InvestigationType.FEATURE_ANALYSIS,
                (
                    "feature",
                    "implement",
                    "analyze",
                    "behaviour",
                    "behavior",
                ),
                0.80,
            ),
        ]

        for investigation_type, keywords, confidence in rules:
            if any(keyword in text for keyword in keywords):
                return investigation_type, confidence

        return InvestigationType.UNKNOWN, 0.40

    def _detect_domain(
        self,
        text: str,
    ) -> tuple[InvestigationDomain, float]:
        rules: list[
            tuple[
                InvestigationDomain,
                tuple[str, ...],
                float,
            ]
        ] = [
            (
                InvestigationDomain.BACKEND,
                (
                    "backend",
                    "server",
                    "repository",
                    "service",
                    "railway",
                ),
                0.95,
            ),
            (
                InvestigationDomain.FRONTEND,
                (
                    "frontend",
                    "ui",
                    "react",
                    "page",
                    "component",
                ),
                0.95,
            ),
            (
                InvestigationDomain.MOBILE,
                (
                    "flutter",
                    "android",
                    "ios",
                    "mobile",
                ),
                0.95,
            ),
            (
                InvestigationDomain.API,
                (
                    "api",
                    "endpoint",
                    "route",
                    "request",
                    "response",
                ),
                0.95,
            ),
            (
                InvestigationDomain.DATABASE,
                (
                    "database",
                    "postgres",
                    "sqlite",
                    "schema",
                    "query",
                ),
                0.95,
            ),
            (
                InvestigationDomain.AUTH,
                (
                    "auth",
                    "login",
                    "jwt",
                    "token",
                    "authentication",
                ),
                0.95,
            ),
            (
                InvestigationDomain.INFRASTRUCTURE,
                (
                    "docker",
                    "deployment",
                    "infra",
                    "kubernetes",
                    "container",
                ),
                0.95,
            ),
        ]

        for domain, keywords, confidence in rules:
            if any(keyword in text for keyword in keywords):
                return domain, confidence

        return InvestigationDomain.UNKNOWN, 0.40


class OllamaIntentClassifier(BaseIntentClassifier):
    """
    Placeholder for future LLM classification.

    Expected flow:

    request
        ↓
    prompt template
        ↓
    ollama
        ↓
    InvestigationIntent
    """

    def classify(
        self,
        request: str,
    ) -> InvestigationIntent:
        raise NotImplementedError(
            "OllamaIntentClassifier is not implemented yet."
        )


class HybridIntentClassifier(BaseIntentClassifier):
    """
    Future strategy:

    1. Rule-based classification
    2. Ollama classification
    3. Confidence reconciliation
    """

    def __init__(
        self,
        fallback_classifier: IntentClassifier | None = None,
    ) -> None:
        self._fallback_classifier = (
            fallback_classifier
            or RuleBasedIntentClassifier()
        )

    def classify(
        self,
        request: str,
    ) -> InvestigationIntent:
        return self._fallback_classifier.classify(
            request,
        )