"""Graph traversal and component algorithms for c03_graph_engine.

BROKEN VARIANT: dijkstra ignores edge weights and returns hop counts.
This causes test_dijkstra_weighted_path to fail.
"""
from __future__ import annotations

import heapq
from collections import deque
from typing import Any

from structures import Graph


def bfs(graph: Graph, source: Any) -> dict[Any, int]:
    """Breadth-first traversal returning hop distances from *source*."""
    if source not in dict(graph._adj):
        return {}

    dist: dict[Any, int] = {source: 0}
    queue: deque[Any] = deque([source])

    while queue:
        u = queue.popleft()
        for v, _ in graph.neighbors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)

    return dist


def dijkstra(graph: Graph, source: Any) -> dict[Any, float]:
    """BROKEN: Ignores edge weights — returns hop counts, not weighted distances.

    Planted defect: the loop accumulates 1.0 per hop instead of the actual
    edge weight. This causes weighted-path tests to return wrong answers.
    """
    if source not in graph._adj:
        return {}

    dist: dict[Any, float] = {source: 0.0}
    # Min-heap of (distance, node)
    heap: list[tuple[float, Any]] = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue  # stale entry
        for v, _w in graph.neighbors(u):
            # BUG: ignoring _w, using hop count of 1 instead of actual weight
            nd = d + 1.0
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    return dist


def connected_components(graph: Graph) -> list[set]:
    """Return connected components of an **undirected** graph."""
    visited: set[Any] = set()
    components: list[set] = []

    for start in graph.nodes():
        if start in visited:
            continue
        component: set[Any] = set()
        queue: deque[Any] = deque([start])
        visited.add(start)
        component.add(start)

        while queue:
            u = queue.popleft()
            for v, _ in graph.neighbors(u):
                if v not in visited:
                    visited.add(v)
                    component.add(v)
                    queue.append(v)

        components.append(component)

    return components
