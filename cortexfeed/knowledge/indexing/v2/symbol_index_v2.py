# File: cortexfeed/knowledge/indexing/v2/symbol_index_v2.py
from __future__ import annotations

import ast
from dataclasses import asdict
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.models import (
    ClassSymbol,
    FunctionSymbol,
    MethodSymbol,
    ImportSymbol,
    RouteSymbol,
    SymbolReference,
    FunctionCall,
    Instantiation,
    AttributeAccess,
    DecoratorUsage,
    InheritanceRelation,
)


class PythonSymbolExtractorV2(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        
        # V1 Extractions
        self.classes: list[ClassSymbol] = []
        self.functions: list[FunctionSymbol] = []
        self.methods: list[MethodSymbol] = []
        self.routes: list[RouteSymbol] = []
        self.imports: list[ImportSymbol] = []

        # V2 Extractions
        self.references: list[SymbolReference] = []
        self.calls: list[FunctionCall] = []
        self.instantiations: list[Instantiation] = []
        self.attributes: list[AttributeAccess] = []
        self.decorators: list[DecoratorUsage] = []
        self.inherits: list[InheritanceRelation] = []

        # Stacks for context tracking
        self._class_stack: list[str] = []
        self._function_stack: list[str] = []

    def _qualified_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._qualified_name(node.value)
            return f"{value_name}.{node.attr}" if value_name else node.attr
        elif isinstance(node, ast.Call):
            return self._qualified_name(node.func)
        return ""

    def _decorator_name(self, node: ast.expr) -> str:
        return self._qualified_name(node)

    def _extract_decorators(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
        decs = []
        for d in node.decorator_list:
            name = self._decorator_name(d)
            if name:
                decs.append(name)
                self.decorators.append(
                    DecoratorUsage(decorator=name, line=d.lineno)
                )
        return decs

    def _extract_routes(self, node: ast.FunctionDef | ast.AsyncFunctionDef, decs: list[str]):
        for d, expr in zip(decs, node.decorator_list):
            if isinstance(expr, ast.Call) and any(d.endswith(m) for m in ('.get', '.post', '.put', '.delete', '.patch')):
                if expr.args and isinstance(expr.args[0], ast.Constant) and isinstance(expr.args[0].value, str):
                    method = d.split('.')[-1].upper()
                    self.routes.append(
                        RouteSymbol(
                            path=expr.args[0].value,
                            method=method,
                            function_name=node.name,
                            line=node.lineno,
                        )
                    )

    def _extract_imports(self, node: ast.Import | ast.ImportFrom):
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports.append(ImportSymbol(module=alias.name, imported=None, line=node.lineno))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                self.imports.append(ImportSymbol(module=module, imported=alias.name, line=node.lineno))

    def visit_Import(self, node: ast.Import):
        self._extract_imports(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self._extract_imports(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        decs = self._extract_decorators(node)
        bases = [self._qualified_name(b) for b in node.bases]
        bases = [b for b in bases if b]
        
        self.classes.append(
            ClassSymbol(
                name=node.name,
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                bases=bases
            )
        )
        
        for parent in bases:
            self.inherits.append(
                InheritanceRelation(
                    class_name=node.name,
                    parent=parent,
                    line=node.lineno
                )
            )

        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        decs = self._extract_decorators(node)
        self._extract_routes(node, decs)
        
        if self._class_stack:
            self.methods.append(
                MethodSymbol(
                    class_name=self._class_stack[-1],
                    name=node.name,
                    line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    decorators=decs
                )
            )
        else:
            self.functions.append(
                FunctionSymbol(
                    name=node.name,
                    line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    decorators=decs
                )
            )

        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_Name(self, node: ast.Name):
        self.references.append(
            SymbolReference(
                symbol=node.id,
                line=node.lineno
            )
        )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        obj_name = self._qualified_name(node.value)
        if obj_name:
            self.attributes.append(
                AttributeAccess(
                    object_name=obj_name,
                    attribute=node.attr,
                    line=node.lineno
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        target = self._qualified_name(node.func)
        caller = self._function_stack[-1] if self._function_stack else "<module>"
        
        if target:
            self.calls.append(
                FunctionCall(
                    caller=caller,
                    target=target,
                    line=node.lineno
                )
            )
            
            target_base = target.split('.')[-1]
            if target_base and target_base[0].isupper():
                self.instantiations.append(
                    Instantiation(
                        class_name=target,
                        line=node.lineno
                    )
                )
                
        self.generic_visit(node)


class SymbolIndexerV2:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)

    def build(self) -> dict[str, Any]:
        files_data = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
                rel_path = str(py_file.relative_to(self.project_root))
                
                extractor = PythonSymbolExtractorV2(rel_path)
                extractor.visit(tree)

                files_data.append({
                    "file_path": rel_path,
                    "classes": [asdict(c) for c in extractor.classes],
                    "functions": [asdict(f) for f in extractor.functions],
                    "methods": [asdict(m) for m in extractor.methods],
                    "routes": [asdict(r) for r in extractor.routes],
                    "imports": [asdict(i) for i in extractor.imports],
                    "references": [asdict(r) for r in extractor.references],
                    "calls": [asdict(c) for c in extractor.calls],
                    "instantiations": [asdict(i) for i in extractor.instantiations],
                    "attributes": [asdict(a) for a in extractor.attributes],
                    "decorators": [asdict(d) for d in extractor.decorators],
                    "inherits": [asdict(i) for i in extractor.inherits],
                })
            except Exception:
                # Skip files that cannot be read or parsed
                continue

        return {
            "project": self.project_root.name,
            "files": files_data
        }


def build_symbol_index_v2(project_root: str | Path) -> dict[str, Any]:
    indexer = SymbolIndexerV2(project_root)
    return indexer.build()