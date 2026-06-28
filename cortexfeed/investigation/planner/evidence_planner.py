# File: cortexfeed/investigation/planner/evidence_planner.py

from __future__ import annotations

from dataclasses import dataclass

from .models import (
    EvidencePlan,
    EvidenceRequirement,
    EvidenceType,
    InvestigationDomain,
    InvestigationIntent,
    InvestigationType,
)


@dataclass(slots=True, frozen=True)
class EvidenceRule:
    investigation_type: InvestigationType
    domain: InvestigationDomain
    requirements: tuple[EvidenceRequirement, ...]


class EvidenceRegistry:
    """
    Central evidence knowledge base.

    Maps:

    (investigation_type, domain)
        ->
    required evidence

    Future:
    - load from yaml/json
    - knowledge graph integration
    - repository_map integration
    """

    def __init__(self) -> None:
        self._rules: list[EvidenceRule] = self._build_rules()

    def get_requirements(
        self,
        investigation_type: InvestigationType,
        domain: InvestigationDomain,
    ) -> list[EvidenceRequirement]:
        for rule in self._rules:
            if (
                rule.investigation_type == investigation_type
                and rule.domain == domain
            ):
                return list(rule.requirements)

        return self._default_requirements()

    def _build_rules(self) -> list[EvidenceRule]:
        return [
            EvidenceRule(
                investigation_type=InvestigationType.DEBUGGING,
                domain=InvestigationDomain.BACKEND,
                requirements=(
                    EvidenceRequirement(
                        evidence_type=EvidenceType.SERVER_LOGS,
                        reason="Identify runtime failures and exceptions.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.API_ROUTES,
                        reason="Verify route definitions and handlers.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.REPOSITORY_CODE,
                        reason="Inspect backend implementation logic.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.STACK_TRACE,
                        reason="Locate failing execution path.",
                    ),
                ),
            ),
            EvidenceRule(
                investigation_type=InvestigationType.DEBUGGING,
                domain=InvestigationDomain.MOBILE,
                requirements=(
                    EvidenceRequirement(
                        evidence_type=EvidenceType.STACK_TRACE,
                        reason="Locate failing widget or service.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.TERMINAL_OUTPUT,
                        reason="Review runtime diagnostics.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.PROJECT_STRUCTURE,
                        reason="Understand code organization.",
                    ),
                ),
            ),
            EvidenceRule(
                investigation_type=InvestigationType.DEBUGGING,
                domain=InvestigationDomain.API,
                requirements=(
                    EvidenceRequirement(
                        evidence_type=EvidenceType.API_ROUTES,
                        reason="Verify endpoint definitions and handlers.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.REPOSITORY_CODE,
                        reason="Inspect handler implementation logic.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.SERVER_LOGS,
                        reason="Correlate requests with backend activity.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.PROJECT_STRUCTURE,
                        reason="Understand project layout and routing structure.",
                    ),
                ),
            ),
            EvidenceRule(
                investigation_type=InvestigationType.TEST_FAILURE,
                domain=InvestigationDomain.UNKNOWN,
                requirements=(
                    EvidenceRequirement(
                        evidence_type=EvidenceType.TEST_RESULTS,
                        reason="Identify failing assertions.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.STACK_TRACE,
                        reason="Locate failure origin.",
                    ),
                ),
            ),
            EvidenceRule(
                investigation_type=InvestigationType.SECURITY,
                domain=InvestigationDomain.AUTH,
                requirements=(
                    EvidenceRequirement(
                        evidence_type=EvidenceType.CONFIG_FILE,
                        reason="Review authentication configuration.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.API_ROUTES,
                        reason="Inspect protected endpoints.",
                    ),
                    EvidenceRequirement(
                        evidence_type=EvidenceType.REPOSITORY_CODE,
                        reason="Review authorization logic.",
                    ),
                ),
            ),
        ]

    def _default_requirements(
        self,
    ) -> list[EvidenceRequirement]:
        return [
            EvidenceRequirement(
                evidence_type=EvidenceType.PROJECT_STRUCTURE,
                reason="Understand repository layout.",
            ),
            EvidenceRequirement(
                evidence_type=EvidenceType.STACK_TRACE,
                reason="Identify failure location.",
            ),
        ]


class EvidencePlanner:
    """
    Produces investigation evidence plans.

    Input:
        InvestigationIntent

    Output:
        EvidencePlan
    """

    def __init__(
        self,
        registry: EvidenceRegistry | None = None,
    ) -> None:
        self._registry = registry or EvidenceRegistry()

    def create_plan(
        self,
        intent: InvestigationIntent,
        available_evidence: set[EvidenceType] | None = None,
    ) -> EvidencePlan:
        available = available_evidence or set()

        required = self._resolve_requirements(intent)

        missing = [
            requirement
            for requirement in required
            if requirement.evidence_type not in available
        ]

        collection_order = self._prioritize(missing)

        return EvidencePlan(
            required=required,
            missing=missing,
            collection_order=collection_order,
        )

    def _resolve_requirements(
        self,
        intent: InvestigationIntent,
    ) -> list[EvidenceRequirement]:
        requirements = self._registry.get_requirements(
            investigation_type=intent.investigation_type,
            domain=intent.domain,
        )

        if requirements:
            return requirements

        if intent.domain != InvestigationDomain.UNKNOWN:
            return self._registry.get_requirements(
                investigation_type=intent.investigation_type,
                domain=InvestigationDomain.UNKNOWN,
            )

        return self._registry._default_requirements()

    def _prioritize(
        self,
        requirements: list[EvidenceRequirement],
    ) -> list[EvidenceRequirement]:
        priority_map = {
            EvidenceType.STACK_TRACE: 1,
            EvidenceType.SERVER_LOGS: 2,
            EvidenceType.TERMINAL_OUTPUT: 3,
            EvidenceType.TEST_RESULTS: 4,
            EvidenceType.API_ROUTES: 5,
            EvidenceType.REPOSITORY_CODE: 6,
            EvidenceType.DATABASE_SCHEMA: 7,
            EvidenceType.NETWORK_TRACE: 8,
            EvidenceType.CONFIG_FILE: 9,
            EvidenceType.PROJECT_STRUCTURE: 10,
        }

        return sorted(
            requirements,
            key=lambda item: priority_map.get(
                item.evidence_type,
                999,
            ),
        )