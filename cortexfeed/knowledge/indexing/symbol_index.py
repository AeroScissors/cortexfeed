# File: cortexfeed/knowledge/indexing/symbol_index.py

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
    }
)


@dataclass(slots=True)
class ImportSymbol:
    module: str
    imported: str | None
    line: int


@dataclass(slots=True)
class FunctionSymbol:
    name: str
    line: int
    end_line: int
    decorators: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MethodSymbol:
    class_name: str
    name: str
    line: int
    end_line: int
    decorators: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ClassSymbol:
    name: str
    line: int
    end_line: int
    bases: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RouteSymbol:
    path: str
    method: str
    function_name: str
    line: int


@dataclass(slots=True)
class FileSymbols:
    file_path: str
    classes: list[ClassSymbol] = field(default_factory=list)
    functions: list[FunctionSymbol] = field(default_factory=list)
    methods: list[MethodSymbol] = field(default_factory=list)
    routes: list[RouteSymbol] = field(default_factory=list)
    imports: list[ImportSymbol] = field(default_factory=list)


class PythonSymbolExtractor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.classes: list[ClassSymbol] = []
        self.functions: list[FunctionSymbol] = []
        self.methods: list[MethodSymbol] = []
        self.routes: list[RouteSymbol] = []

        self._class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases: list[str] = []

        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)

        self.classes.append(
            ClassSymbol(
                name=node.name,
                line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                bases=bases,
            )
        )

        self._class_stack.append(node.name)

        self.generic_visit(node)

        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        decorators = [
            self._decorator_name(decorator)
            for decorator in node.decorator_list
        ]

        if self._class_stack:
            self.methods.append(
                MethodSymbol(
                    class_name=self._class_stack[-1],
                    name=node.name,
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    decorators=decorators,
                )
            )
        else:
            self.functions.append(
                FunctionSymbol(
                    name=node.name,
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    decorators=decorators,
                )
            )

            routes = self._extract_routes(node)

            self.routes.extend(routes)

        self.generic_visit(node)

    def _extract_routes(
        self,
        node: ast.FunctionDef,
    ) -> list[RouteSymbol]:
        discovered: list[RouteSymbol] = []

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            if not isinstance(decorator.func, ast.Attribute):
                continue

            method = decorator.func.attr.upper()

            if method not in {
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            }:
                continue

            if not decorator.args:
                continue

            first_argument = decorator.args[0]

            if not isinstance(first_argument, ast.Constant):
                continue

            if not isinstance(first_argument.value, str):
                continue

            discovered.append(
                RouteSymbol(
                    path=first_argument.value,
                    method=method,
                    function_name=node.name,
                    line=node.lineno,
                )
            )

        return discovered

    @staticmethod
    def _decorator_name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            return node.attr

        if isinstance(node, ast.Call):
            return PythonSymbolExtractor._decorator_name(
                node.func
            )

        return "unknown"


class SymbolIndexer:
    """
    Repository-wide symbol indexer.

    Extracts:
    - classes
    - functions
    - methods
    - imports
    - routes
    """

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project not found: {self.project_root}"
            )

    def build(self) -> dict[str, Any]:
        results: list[dict[str, Any]] = []

        for file_path in self._iter_source_files():
            symbols = self._index_file(file_path)

            results.append(asdict(symbols))

        results.sort(
            key=lambda item: item["file_path"]
        )

        return {
            "project": self.project_root.name,
            "files": results,
        }

    def _iter_source_files(self) -> list[Path]:
        discovered: list[Path] = []

        for extension in SUPPORTED_EXTENSIONS:
            discovered.extend(
                self.project_root.rglob(f"*{extension}")
            )

        return sorted(
            discovered,
            key=lambda path: str(path).lower(),
        )

    def _index_file(
        self,
        file_path: Path,
    ) -> FileSymbols:
        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        tree = ast.parse(
            source,
            filename=str(file_path),
        )

        extractor = PythonSymbolExtractor()
        extractor.visit(tree)

        imports = self._extract_imports(tree)

        return FileSymbols(
            file_path=file_path.relative_to(
                self.project_root
            ).as_posix(),
            classes=extractor.classes,
            functions=extractor.functions,
            methods=extractor.methods,
            routes=extractor.routes,
            imports=imports,
        )

    @staticmethod
    def _extract_imports(
        tree: ast.AST,
    ) -> list[ImportSymbol]:
        imports: list[ImportSymbol] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    imports.append(
                        ImportSymbol(
                            module=imported.name,
                            imported=None,
                            line=node.lineno,
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""

                for imported in node.names:
                    imports.append(
                        ImportSymbol(
                            module=module_name,
                            imported=imported.name,
                            line=node.lineno,
                        )
                    )

        return imports


def build_symbol_index(
    project_root: str | Path,
) -> dict[str, Any]:
    indexer = SymbolIndexer(project_root)

    return indexer.build()