# File: cortexfeed/knowledge/graph/v3/traversal/bfs.py

from __future__ import annotations

from collections import deque


def bfs(
    adjacency: dict[str, list[str]],
    start: str,
) -> list[str]:
    visited: set[str] = set()
    queue: deque[str] = deque([start])
    order: list[str] = []

    while queue:
        node = queue.popleft()

        if node in visited:
            continue

        visited.add(node)
        order.append(node)

        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                queue.append(neighbor)

    return order