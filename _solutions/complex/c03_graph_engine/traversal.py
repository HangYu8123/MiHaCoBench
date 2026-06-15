"""Graph traversal and component algorithms for c03_graph_engine.

Implements:
    bfs                  — hop distances from a source node
    dijkstra             — weighted shortest paths from a source node
    connected_components — connected components of an undirected graph
"""
from __future__ import annotations

import heapq
from collections import deque
from typing import Any

from structures import Graph


def bfs(graph: Graph, source: Any) -> dict[Any, int]:
    """Breadth-first traversal returning hop distances from *source*.

    Parameters
    ----------
    graph:
        Any ``Graph`` instance (directed or undirected).
    source:
        Starting node. Must be present in *graph*.

    Returns
    -------
    dict
        ``{node: hop_distance}`` for every node reachable from *source*,
        including ``{source: 0}``. Unreachable nodes are **omitted**.
    """
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
    """Shortest weighted-path distances from *source* using Dijkstra's algorithm.

    Parameters
    ----------
    graph:
        Any ``Graph`` instance. Edge weights must be non-negative.
    source:
        Starting node. Must be present in *graph*.

    Returns
    -------
    dict
        ``{node: distance}`` for every reachable node, including
        ``{source: 0.0}``. Unreachable nodes are **omitted**.
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
        for v, w in graph.neighbors(u):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    return dist


def connected_components(graph: Graph) -> list[set]:
    """Return connected components of an **undirected** graph.

    Each component is returned as a ``set`` of node identifiers. The order of
    the returned list and the order within each set are unspecified.

    Parameters
    ----------
    graph:
        An undirected ``Graph`` (``directed=False``).

    Returns
    -------
    list[set]
        One set per connected component.
    """
    visited: set[Any] = set()
    components: list[set] = []

    for start in graph.nodes():
        if start in visited:
            continue
        # BFS to find the whole component
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
