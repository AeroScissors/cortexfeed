# File: cortexfeed/knowledge/resolver/file_resolver.py

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

from cortexfeed.knowledge.resolver.dependency_resolver import (
    resolve_dependencies,
)


class FileResolver:
    """
    Repository dependency analysis engine.

    Answers:

    - Which file owns symbol X?
    - Which files import file Y?
    - Which files depend on file Y?
    - Which files are affected by file Y?
    - Shortest dependency path between files
    """

    def __init__(
        self,
        project_root: str | Path,
    ) -> None:
        self.project_root = Path(
            project_root
        ).resolve()

        dependency_data = (
            resolve_dependencies(
                self.project_root
            )
        )

        self.dependencies = (
            dependency_data[
                "file_dependencies"
            ]
        )

        self.forward_graph = (
            self._build_forward_graph()
        )

        self.reverse_graph = (
            self._build_reverse_graph()
        )

    def direct_dependencies(
        self,
        file_path: str,
    ) -> list[str]:
        return sorted(
            self.forward_graph.get(
                file_path,
                set(),
            )
        )

    def direct_dependents(
        self,
        file_path: str,
    ) -> list[str]:
        return sorted(
            self.reverse_graph.get(
                file_path,
                set(),
            )
        )

    def downstream_files(
        self,
        file_path: str,
    ) -> list[str]:
        """
        Files imported by this file,
        recursively.
        """

        visited: set[str] = set()

        queue = deque([file_path])

        while queue:
            current = queue.popleft()

            for dependency in (
                self.forward_graph.get(
                    current,
                    set(),
                )
            ):
                if dependency in visited:
                    continue

                visited.add(
                    dependency
                )

                queue.append(
                    dependency
                )

        return sorted(visited)

    def affected_files(
        self,
        file_path: str,
    ) -> list[str]:
        """
        Files impacted if this file changes.

        Traverses reverse dependency graph.
        """

        visited: set[str] = set()

        queue = deque([file_path])

        while queue:
            current = queue.popleft()

            for dependent in (
                self.reverse_graph.get(
                    current,
                    set(),
                )
            ):
                if dependent in visited:
                    continue

                visited.add(
                    dependent
                )

                queue.append(
                    dependent
                )

        return sorted(visited)

    def dependency_path(
        self,
        source_file: str,
        target_file: str,
    ) -> list[str]:
        """
        Shortest dependency path.

        Example:

        server.py
            ->
        promise_routes.py
            ->
        promise_service.py
        """

        if source_file == target_file:
            return [source_file]

        visited = {
            source_file
        }

        queue = deque(
            [
                (
                    source_file,
                    [source_file],
                )
            ]
        )

        while queue:
            current, path = (
                queue.popleft()
            )

            for dependency in (
                self.forward_graph.get(
                    current,
                    set(),
                )
            ):
                if dependency == target_file:
                    return [
                        *path,
                        dependency,
                    ]

                if dependency in visited:
                    continue

                visited.add(
                    dependency
                )

                queue.append(
                    (
                        dependency,
                        [
                            *path,
                            dependency,
                        ],
                    )
                )

        return []

    def dependency_depth(
        self,
        file_path: str,
    ) -> int:
        """
        Maximum dependency depth.
        """

        visited: set[str] = set()

        def dfs(
            current: str,
            depth: int,
        ) -> int:
            visited.add(current)

            maximum = depth

            for dependency in (
                self.forward_graph.get(
                    current,
                    set(),
                )
            ):
                if dependency in visited:
                    continue

                maximum = max(
                    maximum,
                    dfs(
                        dependency,
                        depth + 1,
                    ),
                )

            return maximum

        return dfs(
            file_path,
            0,
        )

    def dependency_summary(
        self,
        file_path: str,
    ) -> dict[str, Any]:
        direct_dependencies = (
            self.direct_dependencies(
                file_path
            )
        )

        direct_dependents = (
            self.direct_dependents(
                file_path
            )
        )

        affected = (
            self.affected_files(
                file_path
            )
        )

        return {
            "file": file_path,
            "direct_dependencies": (
                direct_dependencies
            ),
            "direct_dependents": (
                direct_dependents
            ),
            "affected_files": (
                affected
            ),
            "dependency_depth": (
                self.dependency_depth(
                    file_path
                )
            ),
        }

    def _build_forward_graph(
        self,
    ) -> dict[str, set[str]]:
        graph: dict[
            str,
            set[str]
        ] = {}

        for dependency in (
            self.dependencies
        ):
            source = dependency[
                "source_file"
            ]

            target = dependency[
                "target_file"
            ]

            graph.setdefault(
                source,
                set(),
            ).add(target)

        return graph

    def _build_reverse_graph(
        self,
    ) -> dict[str, set[str]]:
        graph: dict[
            str,
            set[str]
        ] = {}

        for dependency in (
            self.dependencies
        ):
            source = dependency[
                "source_file"
            ]

            target = dependency[
                "target_file"
            ]

            graph.setdefault(
                target,
                set(),
            ).add(source)

        return graph


def create_file_resolver(
    project_root: str | Path,
) -> FileResolver:
    return FileResolver(
        project_root
    )