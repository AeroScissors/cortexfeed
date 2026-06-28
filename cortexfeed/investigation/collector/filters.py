# File: cortexfeed/investigation/collector/filters.py

from __future__ import annotations

import re


class LogFilter:
    """
    Utilities for reducing log noise while preserving
    investigation-relevant information.

    Future:
    - AI-assisted prioritization
    - Error clustering
    - Stack trace extraction
    - Similar event collapsing
    """

    ERROR_PATTERNS = (
        r"\berror\b",
        r"\bexception\b",
        r"\btraceback\b",
        r"\bfatal\b",
        r"\bfailed\b",
        r"\bfailure\b",
        r"\bpanic\b",
        r"\bcrash\b",
        r"\b404\b",
        r"\b500\b",
    )

    @classmethod
    def extract_errors(
        cls,
        lines: list[str],
    ) -> list[str]:
        """
        Return lines likely containing errors.
        """

        patterns = [
            re.compile(
                pattern,
                re.IGNORECASE,
            )
            for pattern in cls.ERROR_PATTERNS
        ]

        results: list[str] = []

        for line in lines:
            if any(
                pattern.search(line)
                for pattern in patterns
            ):
                results.append(line)

        return results

    @classmethod
    def remove_empty_lines(
        cls,
        lines: list[str],
    ) -> list[str]:
        return [
            line
            for line in lines
            if line.strip()
        ]

    @classmethod
    def deduplicate_consecutive(
        cls,
        lines: list[str],
    ) -> list[str]:
        """
        Remove repeated adjacent log lines.

        Example:

        A
        A
        A
        B

        becomes:

        A
        B
        """

        if not lines:
            return []

        result = [lines[0]]

        for line in lines[1:]:
            if line != result[-1]:
                result.append(line)

        return result

    @classmethod
    def retain_error_context(
        cls,
        lines: list[str],
        *,
        context_before: int = 5,
        context_after: int = 10,
    ) -> list[str]:
        """
        Keep error lines and surrounding context.
        """

        patterns = [
            re.compile(
                pattern,
                re.IGNORECASE,
            )
            for pattern in cls.ERROR_PATTERNS
        ]

        retained_indexes: set[int] = set()

        for index, line in enumerate(lines):
            if any(
                pattern.search(line)
                for pattern in patterns
            ):
                start = max(
                    0,
                    index - context_before,
                )

                end = min(
                    len(lines),
                    index + context_after + 1,
                )

                retained_indexes.update(
                    range(start, end)
                )

        return [
            lines[index]
            for index in sorted(retained_indexes)
        ]

    @classmethod
    def extract_stack_traces(
        cls,
        lines: list[str],
    ) -> list[str]:
        """
        Basic stack trace extraction.

        Works for:
        - Python
        - Dart
        - JavaScript
        - Java

        Can be expanded later.
        """

        traces: list[str] = []

        current_trace: list[str] = []

        collecting = False

        for line in lines:
            normalized = line.lower()

            if (
                "traceback" in normalized
                or "exception" in normalized
                or "stack trace" in normalized
            ):
                collecting = True

            if collecting:
                current_trace.append(line)

                if not line.strip():
                    traces.append(
                        "\n".join(current_trace)
                    )

                    current_trace = []
                    collecting = False

        if current_trace:
            traces.append(
                "\n".join(current_trace)
            )

        return traces

    @classmethod
    def build_investigation_view(
        cls,
        lines: list[str],
    ) -> list[str]:
        """
        Produce a reduced log view optimized
        for investigations.
        """

        cleaned = cls.remove_empty_lines(lines)

        cleaned = cls.deduplicate_consecutive(
            cleaned
        )

        focused = cls.retain_error_context(
            cleaned
        )

        if focused:
            return focused

        return cleaned