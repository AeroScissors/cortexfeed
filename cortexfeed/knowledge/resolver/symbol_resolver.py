# File: cortexfeed/knowledge/resolver/symbol_resolver.py

from __future__ import annotations

import ast
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SymbolDefinition:
    name: str
    symbol_type: str
    file_path: str
    line: int


@dataclass(slots=True)
class SymbolReference:
    symbol_name: str
    file_path: str
    line: int
    context: str


@dataclass(slots=True)
class SymbolUsage:
    definition: SymbolDefinition
    references: list[SymbolReference] = field(
        default_factory=list
    )


class ReferenceVisitor(ast.NodeVisitor):
    def __init__(
        self,
        file_path: str,
    ) -> None:
        self.file_path = file_path
        self.references: list[
            SymbolReference
        ] = []

    def visit_Name(
        self,
        node: ast.Name,
    ) -> None:
        self.references.append(
            SymbolReference(
                symbol_name=node.id,
                file_path=self.file_path,
                line=node.lineno,
                context="name",
            )
        )

        self.generic_visit(node)

    def visit_Call(
        self,
        node: ast.Call,
    ) -> None:
        if isinstance(
            node.func,
            ast.Name,
        ):
            self.references.append(
                SymbolReference(
                    symbol_name=node.func.id,
                    file_path=self.file_path,
                    line=node.lineno,
                    context="call",
                )
            )

        elif isinstance(
            node.func,
            ast.Attribute,
        ):
            self.references.append(
                SymbolReference(
                    symbol_name=node.func.attr,
                    file_path=self.file_path,
                    line=node.lineno,
                    context="call",
                )
            )

        self.generic_visit(node)

    def visit_Attribute(
        self,
        node: ast.Attribute,
    ) -> None:
        self.references.append(
            SymbolReference(
                symbol_name=node.attr,
                file_path=self.file_path,
                line=node.lineno,
                context="attribute",
            )
        )

        self.generic_visit(node)


class DefinitionVisitor(ast.NodeVisitor):
    def __init__(
        self,
        file_path: str,
    ) -> None:
        self.file_path = file_path
        self.definitions: list[
            SymbolDefinition
        ] = []

    def visit_ClassDef(
        self,
        node: ast.ClassDef,
    ) -> None:
        self.definitions.append(
            SymbolDefinition(
                name=node.name,
                symbol_type="class",
                file_path=self.file_path,
                line=node.lineno,
            )
        )

        self.generic_visit(node)

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:
        self.definitions.append(
            SymbolDefinition(
                name=node.name,
                symbol_type="function",
                file_path=self.file_path,
                line=node.lineno,
            )
        )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        self.definitions.append(
            SymbolDefinition(
                name=node.name,
                symbol_type="function",
                file_path=self.file_path,
                line=node.lineno,
            )
        )

        self.generic_visit(node)


class SymbolResolver:
    """
    Repository-wide symbol reference resolver.

    Answers:

    - Where is X defined?
    - Where is X used?
    - What calls X?
    - Which files reference X?

    Produces a cross-reference index used by:

    - Investigation V3
    - Graph Search
    - Root Cause Analysis
    - Context Selection
    """

    def __init__(
        self,
        project_root: str | Path,
    ) -> None:
        self.project_root = Path(
            project_root
        ).resolve()

        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project not found: {self.project_root}"
            )

    def build(
        self,
    ) -> dict[str, Any]:
        definitions: dict[
            str,
            SymbolDefinition
        ] = {}

        references: list[
            SymbolReference
        ] = []

        for file_path in self._python_files():
            relative_path = (
                file_path.relative_to(
                    self.project_root
                ).as_posix()
            )

            source = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            try:
                tree = ast.parse(
                    source,
                    filename=str(file_path),
                )
            except SyntaxError:
                continue

            definition_visitor = (
                DefinitionVisitor(
                    relative_path
                )
            )

            definition_visitor.visit(tree)

            for definition in (
                definition_visitor.definitions
            ):
                definitions[
                    definition.name
                ] = definition

            reference_visitor = (
                ReferenceVisitor(
                    relative_path
                )
            )

            reference_visitor.visit(tree)

            references.extend(
                reference_visitor.references
            )

        usages: list[
            dict[str, Any]
        ] = []

        for (
            symbol_name,
            definition,
        ) in sorted(
            definitions.items()
        ):
            symbol_references = [
                reference
                for reference in references
                if (
                    reference.symbol_name
                    == symbol_name
                )
            ]

            usages.append(
                asdict(
                    SymbolUsage(
                        definition=definition,
                        references=symbol_references,
                    )
                )
            )

        return {
            "project": self.project_root.name,
            "symbol_count": len(
                definitions
            ),
            "reference_count": len(
                references
            ),
            "symbols": usages,
        }

    def find_definition(
        self,
        symbol_name: str,
    ) -> SymbolDefinition | None:
        index = self.build()

        for symbol in index["symbols"]:
            definition = symbol[
                "definition"
            ]

            if (
                definition["name"]
                == symbol_name
            ):
                return SymbolDefinition(
                    **definition
                )

        return None

    def find_references(
        self,
        symbol_name: str,
    ) -> list[SymbolReference]:
        index = self.build()

        for symbol in index["symbols"]:
            definition = symbol[
                "definition"
            ]

            if (
                definition["name"]
                != symbol_name
            ):
                continue

            return [
                SymbolReference(
                    **reference
                )
                for reference in symbol[
                    "references"
                ]
            ]

        return []

    def find_files_using(
        self,
        symbol_name: str,
    ) -> list[str]:
        references = (
            self.find_references(
                symbol_name
            )
        )

        files = {
            reference.file_path
            for reference in references
        }

        return sorted(files)

    def _python_files(
        self,
    ) -> list[Path]:
        return sorted(
            self.project_root.rglob(
                "*.py"
            ),
            key=lambda path: str(
                path
            ).lower(),
        )


def build_symbol_reference_index(
    project_root: str | Path,
) -> dict[str, Any]:
    resolver = SymbolResolver(
        project_root
    )

    return resolver.build()