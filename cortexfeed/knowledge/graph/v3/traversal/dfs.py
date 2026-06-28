# File: cortexfeed/knowledge/graph/v3/traversal/dfs.py

from __future__ import annotations


def dfs(
    adjacency: dict[str, list[str]],
    start: str,
    visited: set[str] | None = None,
) -> list[str]:
    if visited is None:
        visited = set()

    if start in visited:
        return []

    visited.add(start)

    result = [start]

    for neighbor in adjacency.get(start, []):
        result.extend(
            dfs(
                adjacency=adjacency,
                start=neighbor,
                visited=visited,
            )
        )

    return result