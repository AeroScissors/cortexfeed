# File: cortexfeed/knowledge/graph/v3/resolvers/caller_resolver.py

from __future__ import annotations

import ast
from pathlib import Path

from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)


class _MethodCallVisitor(ast.NodeVisitor):
    def __init__(
        self,
        file_path: str,
        symbol_index: dict,
    ) -> None:
        self.file_path = file_path
        self.symbol_index = symbol_index
        self.relationships: list[CallRelationship] = []

        self._current_class: str | None = None
        self._current_method: str | None = None
        self._class_methods: set[str] = set()
        self._local_variables: dict[str, str] = {}

    def _find_symbol_file(
        self,
        class_name: str,
        method_name: str,
    ) -> str:
        files = self.symbol_index.get(
            "files",
            [],
        )

        for file_data in files:
            methods = file_data.get(
                "methods",
                [],
            )

            for method in methods:
                if (
                    method.get("class_name") == class_name
                    and method.get("name") == method_name
                ):
                    return file_data.get(
                        "file_path",
                        "",
                    )

        return ""

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        previous_class = self._current_class

        self._current_class = node.name

        self._class_methods = {
            child.name
            for child in node.body
            if isinstance(child, ast.FunctionDef)
        }

        self.generic_visit(node)

        self._current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous_method = self._current_method

        self._current_method = node.name
        self._local_variables = {}

        self.generic_visit(node)

        self._current_method = previous_method

    def visit_Assign(self, node: ast.Assign) -> None:
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
        ):
            variable_name = node.targets[0].id
            class_name = node.value.func.id

            self._local_variables[variable_name] = class_name

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._current_class is not None and self._current_method is not None:
            if isinstance(node.func, ast.Attribute):
                # self.some_method()
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                    and node.func.attr in self._class_methods
                ):
                    self.relationships.append(
                        CallRelationship(
                            caller_symbol=f"{self._current_class}.{self._current_method}",
                            callee_symbol=f"{self._current_class}.{node.func.attr}",
                            caller_file=self.file_path,
                            callee_file=self.file_path,
                            line_number=node.lineno,
                        )
                    )
                # Service().login()
                elif (
                    isinstance(node.func.value, ast.Call)
                    and isinstance(node.func.value.func, ast.Name)
                ):
                    class_name = node.func.value.func.id
                    method_name = node.func.attr

                    self.relationships.append(
                        CallRelationship(
                            caller_symbol=f"{self._current_class}.{self._current_method}",
                            callee_symbol=f"{class_name}.{method_name}",
                            caller_file=self.file_path,
                            callee_file=self._find_symbol_file(
                                class_name,
                                method_name,
                            ),
                            line_number=node.lineno,
                        )
                    )
                # service.login()
                elif isinstance(node.func.value, ast.Name):
                    variable_name = node.func.value.id

                    if variable_name in self._local_variables:
                        class_name = self._local_variables[variable_name]

                        self.relationships.append(
                            CallRelationship(
                                caller_symbol=f"{self._current_class}.{self._current_method}",
                                callee_symbol=f"{class_name}.{node.func.attr}",
                                caller_file=self.file_path,
                                callee_file=self._find_symbol_file(
                                    class_name,
                                    node.func.attr,
                                ),
                                line_number=node.lineno,
                            )
                        )

        self.generic_visit(node)


class CallerResolver:
    def resolve(
        self,
        project_root: Path,
        symbol_index: dict,
        import_index: dict,
    ) -> list[CallRelationship]:
        relationships: list[CallRelationship] = []

        for file_path in project_root.rglob("*.py"):
            try:
                source = file_path.read_text(
                    encoding="utf-8",
                )

                tree = ast.parse(source)

                visitor = _MethodCallVisitor(
                    file_path=str(file_path),
                    symbol_index=symbol_index,
                )

                visitor.visit(tree)

                relationships.extend(
                    visitor.relationships
                )

            except Exception:
                continue

        return relationships