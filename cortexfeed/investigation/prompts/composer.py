# File: cortexfeed/investigation/prompts/composer.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .templates import PromptTemplate, get_template


@dataclass
class PromptPackage:
    """
    Structured prompt package produced by the investigation system.

    This object is the handoff between the investigation layer
    and the formatter layer.
    """

    template_name: str
    system_instructions: str
    sections: Dict[str, Any] = field(default_factory=dict)


class PromptComposer:
    """
    Builds prompt packages from investigation artifacts.

    Responsibilities:

    - select template
    - merge evidence
    - merge facts
    - merge hypotheses
    - merge timeline
    - generate structured package
    """

    def select_template(
        self,
        template_name: Optional[str] = None,
    ) -> PromptTemplate:
        """
        Resolve template.

        Falls back to debugging template.
        """

        if not template_name:
            return get_template("debugging")

        return get_template(template_name)

    def compose(
        self,
        *,
        template_name: str = "debugging",
        project: str = "",
        current_issue: str = "",
        facts: Optional[List[Any]] = None,
        hypotheses: Optional[List[Any]] = None,
        root_cause: Optional[Any] = None,
        evidence: Optional[List[Any]] = None,
        timeline: Optional[List[Any]] = None,
        failed_attempts: Optional[List[Any]] = None,
        open_questions: Optional[List[Any]] = None,
        task: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> PromptPackage:
        """
        Build a complete prompt package.

        The package remains model-agnostic.
        Rendering is handled by formatter.py.
        """

        template = self.select_template(template_name)

        sections: Dict[str, Any] = {
            "project": project,
            "current_issue": current_issue,
            "verified_facts": self._normalize_list(facts),
            "relevant_evidence": self._normalize_list(evidence),
            "active_hypotheses": self._normalize_list(hypotheses),
            "timeline": self._normalize_list(timeline),
            "failed_attempts": self._normalize_list(failed_attempts),
            "open_questions": self._normalize_list(open_questions),
            "task": task,
        }

        if root_cause is not None:
            sections["likely_root_cause"] = getattr(
                root_cause, "likely_root_cause", str(root_cause)
            )
            sections["confidence"] = getattr(
                root_cause, "confidence", None
            )
            sections["alternatives"] = self._normalize_list(
                getattr(root_cause, "alternatives", None)
            )
            sections["reasoning"] = getattr(
                root_cause, "reasoning", None
            )

        if extra_context:
            sections.update(extra_context)

        return PromptPackage(
            template_name=template.name,
            system_instructions=template.system_instructions,
            sections=sections,
        )

    def build_from_session(
        self,
        session: Any,
        template_name: str = "debugging",
    ) -> PromptPackage:
        """
        Build a prompt package directly from an
        InvestigationSession object.

        Session interfaces are intentionally loose
        so the prompt subsystem does not tightly
        couple to session internals.
        """

        project = getattr(session, "project_name", "")

        current_issue = getattr(
            session,
            "current_issue",
            "",
        )

        facts = getattr(
            session,
            "facts",
            [],
        )

        evidence = getattr(
            session,
            "evidence",
            [],
        )

        hypotheses = getattr(
            session,
            "hypotheses",
            [],
        )

        root_cause = getattr(
            session,
            "root_cause",
            None,
        )

        timeline = getattr(
            session,
            "timeline",
            [],
        )

        return self.compose(
            template_name=template_name,
            project=project,
            current_issue=current_issue,
            facts=facts,
            hypotheses=hypotheses,
            root_cause=root_cause,
            evidence=evidence,
            timeline=timeline,
        )

    def extract_relevant_context(
        self,
        *,
        facts: List[Any],
        evidence: List[Any],
        hypotheses: List[Any],
        max_items: int = 25,
    ) -> Dict[str, List[Any]]:
        """
        Reduce prompt noise.

        Future versions may use scoring,
        embeddings, or ranking.

        Current implementation keeps the
        most recent items.
        """

        return {
            "facts": facts[:max_items],
            "evidence": evidence[:max_items],
            "hypotheses": hypotheses[:max_items],
        }

    @staticmethod
    def _normalize_list(
        values: Optional[List[Any]],
    ) -> List[Any]:
        """
        Convert None to an empty list.
        """

        if values is None:
            return []

        return list(values)