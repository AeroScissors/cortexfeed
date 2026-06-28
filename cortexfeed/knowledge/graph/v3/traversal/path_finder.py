# File: cortexfeed/knowledge/graph/v3/traversal/path_finder.py

from __future__ import annotations

from collections import deque


class PathFinder:
    def shortest_path(
        self,
        adjacency: dict[str, list[str]],
        start: str,
        target: str,
    ) -> list[str]:
        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            node, path = queue.popleft()

            if node == target:
                return path

            for neighbor in adjacency.get(node, []):
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

        return []