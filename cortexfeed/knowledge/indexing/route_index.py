# File: cortexfeed/knowledge/indexing/route_index.py

from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".dart",
        ".js",
        ".ts",
    }
)


@dataclass(slots=True)
class RouteDefinition:
    method: str
    path: str
    handler: str
    file_path: str
    line: int
    parameters: list[str] = field(
        default_factory=list
    )
    framework: str = "unknown"


class RouteIndexer:
    """
    Repository route discovery engine.

    Supports:

    - Flask (@app.route, @bp.route, methods kwarg)
    - FastAPI (@app.get, @app.post, etc.)
    - Shelf (router.get('/path', ...))
    - Express (app.get('/path', ...))
    - Generic REST patterns
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

    def build(self) -> dict[str, Any]:
        routes: list[RouteDefinition] = []

        for file_path in self._source_files():
            suffix = file_path.suffix.lower()

            try:
                if suffix == ".py":
                    routes.extend(
                        self._python_routes(file_path)
                    )

                elif suffix == ".dart":
                    routes.extend(
                        self._dart_routes(file_path)
                    )

                elif suffix in {".js", ".ts"}:
                    routes.extend(
                        self._javascript_routes(file_path)
                    )

            except Exception:
                continue

        routes.sort(
            key=lambda item: (
                item.path,
                item.method,
                item.file_path,
            )
        )

        return {
            "project": self.project_root.name,
            "route_count": len(routes),
            "routes": [
                asdict(route)
                for route in routes
            ],
        }

    def save(self, output_file: str | Path) -> Path:
        output_file = Path(output_file)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_file.open("w", encoding="utf-8") as handle:
            json.dump(
                self.build(),
                handle,
                indent=2,
                ensure_ascii=False,
            )

        return output_file

    def _python_routes(
        self,
        file_path: Path,
    ) -> list[RouteDefinition]:
        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        tree = ast.parse(
            source,
            filename=str(file_path),
        )

        routes: list[RouteDefinition] = []

        relative_path = (
            file_path.relative_to(self.project_root).as_posix()
        )

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            for decorator in node.decorator_list:
                route = self._extract_python_route(
                    decorator,
                    node,
                    relative_path,
                )

                if route is not None:
                    routes.append(route)

        return routes

    def _extract_python_route(
        self,
        decorator: ast.expr,
        function: ast.FunctionDef,
        file_path: str,
    ) -> RouteDefinition | None:
        if not isinstance(decorator, ast.Call):
            return None

        if not isinstance(decorator.func, ast.Attribute):
            return None

        attr = decorator.func.attr.upper()

        # ── Pattern 1: @app.route('/path', methods=['GET', 'POST'])
        # ── or @bp.route('/path', methods=['POST'])
        if attr == "ROUTE":
            if not decorator.args:
                return None

            argument = decorator.args[0]

            if not isinstance(argument, ast.Constant):
                return None

            if not isinstance(argument.value, str):
                return None

            route_path = argument.value

            # extract methods from methods=[...] kwarg
            methods = self._extract_methods_kwarg(decorator)

            if not methods:
                # default to GET if no methods kwarg
                methods = ["GET"]

            # register one RouteDefinition per method
            # return the first and let caller loop for multi-method
            # (we return list via _python_routes so just return first here,
            #  but we need to handle multi — see note below)
            return RouteDefinition(
                method=methods[0],
                path=route_path,
                handler=function.name,
                file_path=file_path,
                line=function.lineno,
                parameters=self._path_parameters(route_path),
                framework="flask",
            )

        # ── Pattern 2: @app.get('/path'), @app.post('/path') etc. (FastAPI style)
        if attr in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            if not decorator.args:
                return None

            argument = decorator.args[0]

            if not isinstance(argument, ast.Constant):
                return None

            if not isinstance(argument.value, str):
                return None

            route_path = argument.value

            return RouteDefinition(
                method=attr,
                path=route_path,
                handler=function.name,
                file_path=file_path,
                line=function.lineno,
                parameters=self._path_parameters(route_path),
                framework="fastapi",
            )

        return None

    def _extract_methods_kwarg(
        self,
        decorator: ast.Call,
    ) -> list[str]:
        """
        Extract HTTP methods from methods=['GET', 'POST'] kwarg.
        """
        for keyword in decorator.keywords:
            if keyword.arg != "methods":
                continue

            if not isinstance(keyword.value, ast.List):
                continue

            methods = []
            for element in keyword.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    methods.append(element.value.upper())

            return methods

        return []

    def _python_routes(
        self,
        file_path: Path,
    ) -> list[RouteDefinition]:
        """
        Override to handle multi-method routes properly.
        """
        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        tree = ast.parse(
            source,
            filename=str(file_path),
        )

        routes: list[RouteDefinition] = []

        relative_path = (
            file_path.relative_to(self.project_root).as_posix()
        )

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue

                attr = decorator.func.attr.upper()

                if attr == "ROUTE":
                    # Flask @app.route or @bp.route
                    if not decorator.args:
                        continue
                    arg = decorator.args[0]
                    if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                        continue

                    route_path = arg.value
                    methods = self._extract_methods_kwarg(decorator) or ["GET"]

                    for method in methods:
                        routes.append(
                            RouteDefinition(
                                method=method,
                                path=route_path,
                                handler=node.name,
                                file_path=relative_path,
                                line=node.lineno,
                                parameters=self._path_parameters(route_path),
                                framework="flask",
                            )
                        )

                elif attr in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    # FastAPI @app.get, @app.post etc.
                    if not decorator.args:
                        continue
                    arg = decorator.args[0]
                    if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                        continue

                    route_path = arg.value
                    routes.append(
                        RouteDefinition(
                            method=attr,
                            path=route_path,
                            handler=node.name,
                            file_path=relative_path,
                            line=node.lineno,
                            parameters=self._path_parameters(route_path),
                            framework="fastapi",
                        )
                    )

        return routes

    def _dart_routes(
        self,
        file_path: Path,
    ) -> list[RouteDefinition]:
        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        relative_path = (
            file_path.relative_to(self.project_root).as_posix()
        )

        routes: list[RouteDefinition] = []

        pattern = re.compile(
            r"router\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE,
        )

        for line_number, line in enumerate(
            source.splitlines(),
            start=1,
        ):
            match = pattern.search(line)

            if match is None:
                continue

            method = match.group(1).upper()
            route_path = match.group(2)

            routes.append(
                RouteDefinition(
                    method=method,
                    path=route_path,
                    handler="unknown",
                    file_path=relative_path,
                    line=line_number,
                    parameters=self._path_parameters(route_path),
                    framework="shelf",
                )
            )

        return routes

    def _javascript_routes(
        self,
        file_path: Path,
    ) -> list[RouteDefinition]:
        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        relative_path = (
            file_path.relative_to(self.project_root).as_posix()
        )

        routes: list[RouteDefinition] = []

        pattern = re.compile(
            r"(app|router)\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE,
        )

        for line_number, line in enumerate(
            source.splitlines(),
            start=1,
        ):
            match = pattern.search(line)

            if match is None:
                continue

            method = match.group(2).upper()
            route_path = match.group(3)

            routes.append(
                RouteDefinition(
                    method=method,
                    path=route_path,
                    handler="unknown",
                    file_path=relative_path,
                    line=line_number,
                    parameters=self._path_parameters(route_path),
                    framework="express",
                )
            )

        return routes

    @staticmethod
    def _path_parameters(
        route_path: str,
    ) -> list[str]:
        parameters = []

        parameters.extend(
            re.findall(
                r"<([^>]+)>",
                route_path,
            )
        )

        parameters.extend(
            re.findall(
                r":([a-zA-Z_][a-zA-Z0-9_]*)",
                route_path,
            )
        )

        return sorted(set(parameters))

    def _source_files(self) -> list[Path]:
        files: list[Path] = []

        for extension in SUPPORTED_EXTENSIONS:
            files.extend(
                self.project_root.rglob(f"*{extension}")
            )

        return sorted(
            files,
            key=lambda item: str(item).lower(),
        )


def build_route_index(
    project_root: str | Path,
) -> dict[str, Any]:
    indexer = RouteIndexer(project_root)
    return indexer.build()


def save_route_index(
    project_root: str | Path,
    output_file: str | Path,
) -> Path:
    indexer = RouteIndexer(project_root)
    return indexer.save(output_file)