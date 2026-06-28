# File: cortexfeed/investigation/collector/project_collector.py

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .base import RepositoryCollector
from .models import Evidence, EvidenceType


class ProjectCollector(RepositoryCollector):
    """
    Collects repository-level evidence.

    Responsibilities:
    - Scan repository
    - Build project summary
    - Discover potentially relevant files
    - Produce investigation-ready metadata

    Future:
    - Repository graph integration
    - Embedding-based retrieval
    - Dependency analysis
    """

    DEFAULT_EXTENSIONS = {
        ".py",
        ".dart",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".sql",
        ".md",
    }

    EXCLUDED_DIRECTORIES = {
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        ".pytest_cache",
        ".dart_tool",
        "build",
        "dist",
        "node_modules",
        ".venv",
        "venv",
    }

    def __init__(
        self,
        project_root: str | Path,
        *,
        allowed_extensions: set[str] | None = None,
    ) -> None:
        super().__init__(project_root)

        self.allowed_extensions = (
            allowed_extensions
            if allowed_extensions is not None
            else self.DEFAULT_EXTENSIONS
        )

    def collect(self) -> list[Evidence]:
        self.validate_root()

        files = self._scan_repository()

        summary = self._build_summary(files)

        summary_evidence = Evidence.create(
            evidence_type=EvidenceType.PROJECT_SUMMARY,
            source="project_collector",
            path=str(self.project_root),
            content=self._format_summary(summary),
            metadata=summary,
        )

        file_evidence = [
            Evidence.create(
                evidence_type=EvidenceType.PROJECT_FILE,
                source="project_collector",
                path=str(file_path),
                content=str(
                    file_path.relative_to(self.project_root)
                ),
                metadata={
                    "extension": file_path.suffix,
                },
            )
            for file_path in files
        ]

        return [summary_evidence, *file_evidence]

    def discover_relevant_files(
        self,
        keywords: list[str],
        *,
        max_results: int = 25,
    ) -> list[Path]:
        self.validate_root()

        normalized_keywords = [
            keyword.lower()
            for keyword in keywords
        ]

        scored_files: list[tuple[int, Path]] = []

        for file_path in self._scan_repository():
            score = self._score_file(
                file_path,
                normalized_keywords,
            )

            if score > 0:
                scored_files.append(
                    (score, file_path)
                )

        scored_files.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            path
            for _, path in scored_files[:max_results]
        ]

    def _scan_repository(self) -> list[Path]:
        discovered: list[Path] = []

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue

            if self._is_excluded(path):
                continue

            if path.suffix.lower() not in self.allowed_extensions:
                continue

            discovered.append(path)

        return sorted(discovered)

    def _is_excluded(self, path: Path) -> bool:
        return any(
            part in self.EXCLUDED_DIRECTORIES
            for part in path.parts
        )

    def _build_summary(
        self,
        files: list[Path],
    ) -> dict[str, object]:
        extension_counts = Counter(
            file.suffix.lower()
            for file in files
        )

        return {
            "project_root": str(self.project_root),
            "file_count": len(files),
            "extensions": dict(extension_counts),
            "languages": self._detect_languages(
                extension_counts
            ),
        }

    def _detect_languages(
        self,
        extension_counts: Counter[str],
    ) -> list[str]:
        mapping = {
            ".py": "Python",
            ".dart": "Dart",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".sql": "SQL",
        }

        languages: set[str] = set()

        for extension in extension_counts:
            language = mapping.get(extension)

            if language:
                languages.add(language)

        return sorted(languages)

    def _format_summary(
        self,
        summary: dict[str, object],
    ) -> str:
        lines = [
            f"Project Root: {summary['project_root']}",
            f"File Count: {summary['file_count']}",
            "",
            "Languages:",
        ]

        for language in summary["languages"]:
            lines.append(f"- {language}")

        lines.append("")
        lines.append("Extensions:")

        extensions = summary["extensions"]

        for extension, count in sorted(
            extensions.items()
        ):
            lines.append(
                f"- {extension}: {count}"
            )

        return "\n".join(lines)

    def _score_file(
        self,
        file_path: Path,
        keywords: list[str],
    ) -> int:
        score = 0

        path_text = str(file_path).lower()

        for keyword in keywords:
            if keyword in path_text:
                score += 10

        return score