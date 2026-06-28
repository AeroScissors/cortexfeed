# File: cortexfeed/investigation/prompts/formatter.py

from __future__ import annotations

from typing import Any, Iterable, List

from .composer import PromptPackage


class PromptFormatter:
    """
    Render PromptPackage objects into model-specific prompts.

    Responsibilities:

    - markdown rendering
    - plain text rendering
    - Claude optimization
    - Gemini optimization
    - ChatGPT optimization
    - Local model optimization
    """

    def to_markdown(
        self,
        package: PromptPackage,
    ) -> str:
        """
        Render as structured markdown.
        """

        lines: List[str] = []

        lines.append("# SYSTEM INSTRUCTIONS")
        lines.append("")
        lines.append(package.system_instructions)
        lines.append("")

        for section_name, value in package.sections.items():
            rendered = self._render_value(value)
            # Skip sections that have no meaningful content
            if not rendered or rendered == ["None"]:
                continue

            lines.append(
                f"# {self._title(section_name)}"
            )
            lines.append("")
            lines.extend(rendered)
            lines.append("")

        return "\n".join(lines).strip()

    def to_text(
        self,
        package: PromptPackage,
    ) -> str:
        """
        Render as plain text.
        """

        lines: List[str] = []

        lines.append("SYSTEM INSTRUCTIONS")
        lines.append("-------------------")
        lines.append(package.system_instructions)
        lines.append("")

        for section_name, value in package.sections.items():
            rendered = self._render_value(value)
            if not rendered or rendered == ["None"]:
                continue

            title = self._title(section_name)
            lines.append(title)
            lines.append("-" * len(title))
            lines.extend(rendered)
            lines.append("")

        return "\n".join(lines).strip()

    def to_claude(
        self,
        package: PromptPackage,
    ) -> str:
        """
        Claude performs best with clear
        investigation structure and explicit
        reasoning constraints.
        """

        prompt = self.to_markdown(package)

        return (
            "You are conducting a structured "
            "software investigation.\n\n"
            "Rules:\n"
            "- Separate facts from assumptions.\n"
            "- Identify missing evidence.\n"
            "- Explain reasoning.\n"
            "- State confidence levels.\n"
            "- Do not invent implementation details.\n\n"
            f"{prompt}"
        )

    def to_gemini(
        self,
        package: PromptPackage,
    ) -> str:
        """
        Gemini benefits from explicit
        context organization and task focus.
        """

        prompt = self.to_markdown(package)

        return (
            "Analyze the investigation context "
            "below and produce the most accurate "
            "technical assessment possible.\n\n"
            "Focus on:\n"
            "1. Root cause analysis\n"
            "2. Missing evidence\n"
            "3. Recommended next investigation steps\n"
            "4. Architectural observations\n\n"
            f"{prompt}"
        )

    def to_chatgpt(
        self,
        package: PromptPackage,
    ) -> str:
        """
        ChatGPT-oriented rendering.
        """

        prompt = self.to_markdown(package)

        return (
            "Review the investigation package "
            "and provide a structured engineering "
            "analysis.\n\n"
            "Prioritize verified evidence over "
            "assumptions.\n\n"
            f"{prompt}"
        )

    def to_local(
        self,
        package: PromptPackage,
    ) -> str:
        """
        Local models often perform better with
        concise prompts and reduced verbosity.
        """

        prompt = self.to_text(package)

        return (
            "Task: Analyze the investigation.\n\n"
            f"{prompt}"
        )

    def format(
        self,
        package: PromptPackage,
        target: str = "markdown",
    ) -> str:
        """
        Generic formatter entrypoint.
        """

        target = target.lower()

        if target == "markdown":
            return self.to_markdown(package)

        if target == "text":
            return self.to_text(package)

        if target == "claude":
            return self.to_claude(package)

        if target == "gemini":
            return self.to_gemini(package)

        if target == "chatgpt":
            return self.to_chatgpt(package)

        if target == "local":
            return self.to_local(package)

        raise ValueError(
            f"Unsupported formatter target: {target}"
        )

    def _render_value(
        self,
        value: Any,
    ) -> List[str]:
        """
        Render arbitrary values into prompt text.
        """

        if value is None:
            return ["None"]

        if isinstance(value, str):
            return [value]

        if isinstance(value, dict):
            return [
                f"- {key}: {item}"
                for key, item in value.items()
            ]

        if isinstance(value, Iterable) and not isinstance(
            value,
            (str, bytes),
        ):
            items = list(value)

            if not items:
                return ["None"]

            return [
                f"- {item}"
                for item in items
            ]

        return [str(value)]

    @staticmethod
    def _title(
        value: str,
    ) -> str:
        """
        Convert section names into readable titles.
        """

        return (
            value.replace("_", " ")
            .strip()
            .upper()
        )