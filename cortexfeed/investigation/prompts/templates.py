# File: cortexfeed/investigation/prompts/templates.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class PromptTemplate:
    """
    Defines the structure of a prompt.

    Templates decide WHAT information should appear
    in the final prompt, not HOW it is rendered.
    """

    name: str
    description: str
    system_instructions: str
    sections: List[str] = field(default_factory=list)


DEBUGGING_TEMPLATE = PromptTemplate(
    name="debugging",
    description="General software debugging and root cause investigation.",
    system_instructions=(
        "Act as a senior software engineer conducting a structured "
        "investigation. Prioritize verified facts over assumptions. "
        "Identify root causes, missing evidence, and next actions."
    ),
    sections=[
        "project",
        "current_issue",
        "verified_facts",
        "relevant_evidence",
        "timeline",
        "failed_attempts",
        "active_hypotheses",
        "likely_root_cause",
        "confidence",
        "alternatives",
        "reasoning",
        "open_questions",
        "task",
    ],
)


CODE_REVIEW_TEMPLATE = PromptTemplate(
    name="code_review",
    description="Code quality, correctness, maintainability, and risk review.",
    system_instructions=(
        "Act as a senior reviewer. Evaluate correctness, architecture, "
        "maintainability, performance, security, and testing concerns."
    ),
    sections=[
        "project",
        "review_scope",
        "relevant_files",
        "architecture_context",
        "known_constraints",
        "observations",
        "risks",
        "task",
    ],
)


FEATURE_IMPLEMENTATION_TEMPLATE = PromptTemplate(
    name="feature_implementation",
    description="Design and implementation planning for new features.",
    system_instructions=(
        "Act as a senior software architect. Produce an implementation plan "
        "that fits the existing codebase and constraints."
    ),
    sections=[
        "project",
        "feature_request",
        "requirements",
        "existing_architecture",
        "relevant_files",
        "constraints",
        "open_questions",
        "task",
    ],
)


ARCHITECTURE_REVIEW_TEMPLATE = PromptTemplate(
    name="architecture_review",
    description="System architecture analysis and improvement recommendations.",
    system_instructions=(
        "Act as a principal engineer. Evaluate scalability, maintainability, "
        "modularity, fault tolerance, and long-term system evolution."
    ),
    sections=[
        "project",
        "architecture_overview",
        "current_design",
        "constraints",
        "known_issues",
        "improvement_opportunities",
        "task",
    ],
)


ROOT_CAUSE_TEMPLATE = PromptTemplate(
    name="root_cause_analysis",
    description="Deep investigation focused on identifying root causes.",
    system_instructions=(
        "Act as an incident investigator. Separate evidence from theory. "
        "Identify the most likely root causes and explain confidence levels."
    ),
    sections=[
        "project",
        "incident",
        "verified_facts",
        "evidence",
        "timeline",
        "hypotheses",
        "disproved_hypotheses",
        "missing_evidence",
        "task",
    ],
)


DEFAULT_TEMPLATE = DEBUGGING_TEMPLATE


TEMPLATES: Dict[str, PromptTemplate] = {
    DEBUGGING_TEMPLATE.name: DEBUGGING_TEMPLATE,
    CODE_REVIEW_TEMPLATE.name: CODE_REVIEW_TEMPLATE,
    FEATURE_IMPLEMENTATION_TEMPLATE.name: FEATURE_IMPLEMENTATION_TEMPLATE,
    ARCHITECTURE_REVIEW_TEMPLATE.name: ARCHITECTURE_REVIEW_TEMPLATE,
    ROOT_CAUSE_TEMPLATE.name: ROOT_CAUSE_TEMPLATE,
}


def get_template(name: str) -> PromptTemplate:
    """
    Return a template by name.

    Falls back to the debugging template if the
    requested template does not exist.
    """

    return TEMPLATES.get(name, DEFAULT_TEMPLATE)


def list_templates() -> List[str]:
    """
    Return all available template names.
    """

    return sorted(TEMPLATES.keys())