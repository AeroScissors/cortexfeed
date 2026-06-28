# File: cortexfeed/knowledge/resolver/dependency_resolver.py

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.indexing.symbol_index import build_symbol_index


@dataclass(slots=True)
class FileDependency:
    source_file: str
    target_file: str
    dependency_type: str


@dataclass(slots=True)
class SymbolDependency:
    source_file: str
    source_symbol: str
    target_module: str
    target_symbol: str | None


@dataclass(slots=True)
class DependencyResult:
    file_dependencies: list[FileDependency] = field(
        default_factory=list
    )
    symbol_dependencies: list[SymbolDependency] = field(
        default_factory=list
    )


class DependencyResolver:
    """
    Resolves repository dependencies.

    Produces:

    - file -> file dependencies
    - symbol -> symbol dependencies
    - import relationships

    Used by graph_builder.py.
    """

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project root not found: {self.project_root}"
            )

    def resolve(self) -> dict[str, Any]:
        symbol_index = build_symbol_index(
            self.project_root
        )

        result = DependencyResult()

        repository_files = self._build_file_lookup()

        for file_data in symbol_index["files"]:
            source_file = file_data["file_path"]

            for import_data in file_data["imports"]:
                target_file = self._resolve_import_file(
                    import_data["module"],
                    repository_files,
                )

                if target_file is not None:
                    result.file_dependencies.append(
                        FileDependency(
                            source_file=source_file,
                            target_file=target_file,
                            dependency_type="import",
                        )
                    )

                result.symbol_dependencies.append(
                    SymbolDependency(
                        source_file=source_file,
                        source_symbol=source_file,
                        target_module=import_data["module"],
                        target_symbol=import_data["imported"],
                    )
                )

        return {
            "project": self.project_root.name,
            "file_dependencies": [
                asdict(item)
                for item in sorted(
                    result.file_dependencies,
                    key=lambda dependency: (
                        dependency.source_file,
                        dependency.target_file,
                    ),
                )
            ],
            "symbol_dependencies": [
                asdict(item)
                for item in sorted(
                    result.symbol_dependencies,
                    key=lambda dependency: (
                        dependency.source_file,
                        dependency.target_module,
                    ),
                )
            ],
        }

    def _build_file_lookup(
        self,
    ) -> dict[str, str]:
        lookup: dict[str, str] = {}

        for file_path in self.project_root.rglob("*.py"):
            relative = file_path.relative_to(
                self.project_root
            ).as_posix()

            module_name = relative.removesuffix(
                ".py"
            ).replace("/", ".")

            lookup[module_name] = relative

            if module_name.endswith(".__init__"):
                package_name = module_name.removesuffix(
                    ".__init__"
                )
                lookup[package_name] = relative

        return lookup

    def _resolve_import_file(
        self,
        module_name: str,
        repository_files: dict[str, str],
    ) -> str | None:
        if not module_name:
            return None

        if module_name in repository_files:
            return repository_files[module_name]

        parts = module_name.split(".")

        while len(parts) > 1:
            parts.pop()

            candidate = ".".join(parts)

            if candidate in repository_files:
                return repository_files[candidate]

        return None


def resolve_dependencies(
    project_root: str | Path,
) -> dict[str, Any]:
    resolver = DependencyResolver(project_root)

    return resolver.resolve()