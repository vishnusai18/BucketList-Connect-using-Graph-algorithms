"""
algorithms.py

This file codes comtains algorithms for traversal for BFS,DFS etc
"""

from __future__ import annotations

from collections import deque


def bfs(
    graph: dict[str, set[str]],
    start_node: str,
) -> tuple[list[str], dict[str, int], dict[str, str | None]]:
    """
    Breadth-First Search.

    BFS explores the graph level by level from the starting node.

    Returns:
    - visit_order
    - distance from start node
    - parent mapping
    """
    if start_node not in graph:
        return [], {}, {}

    visited = {start_node}
    distance = {start_node: 0}
    parent: dict[str, str | None] = {start_node: None}
    visit_order = []

    queue = deque([start_node])

    while queue:
        current = queue.popleft()
        visit_order.append(current)

        for neighbor in sorted(graph[current]):
            if neighbor not in visited:
                visited.add(neighbor)
                distance[neighbor] = distance[current] + 1
                parent[neighbor] = current
                queue.append(neighbor)

    return visit_order, distance, parent


def dfs(
    graph: dict[str, set[str]],
    start_node: str,
) -> list[str]:
    """
    Depth-First Search.

    DFS explores one branch deeply before backtracking.
    """
    if start_node not in graph:
        return []

    visited = set()
    visit_order = []

    def dfs_recursive(node: str) -> None:
        visited.add(node)
        visit_order.append(node)

        for neighbor in sorted(graph[node]):
            if neighbor not in visited:
                dfs_recursive(neighbor)

    dfs_recursive(start_node)

    return visit_order


def connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    """
    Find connected components in an undirected graph.

    Each connected component is a community of connected users.
    """
    visited = set()
    components = []

    for node in sorted(graph.keys()):
        if node in visited:
            continue

        component = []
        stack = [node]
        visited.add(node)

        while stack:
            current = stack.pop()
            component.append(current)

            for neighbor in sorted(graph[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        components.append(component)

    components.sort(key=len, reverse=True)

    return components


def shortest_path_bfs(
    graph: dict[str, set[str]],
    start_node: str,
    target_node: str,
) -> list[str]:
    """
    Find the shortest path between two nodes using BFS.
    """
    if start_node not in graph or target_node not in graph:
        return []

    _, _, parent = bfs(graph, start_node)

    if target_node not in parent:
        return []

    path = []
    current: str | None = target_node

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return path