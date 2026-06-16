"""
traversal.py — bfs, dijkstra, connected_components
"""
from __future__ import annotations
from collections import deque
import heapq
from typing import Any

from structures import Graph


def bfs(graph: Graph, source: Any) -> dict:
    """
    Breadth-first traversal from *source*.

    Returns a dict mapping each reachable node (including *source*) to its
    hop distance (number of edges).  *source* maps to 0.  Unreachable nodes
    are omitted.
    """
    dist: dict = {source: 0}
    queue: deque = deque([source])
    while queue:
        node = queue.popleft()
        for neighbor, _weight in graph.neighbors(node):
            if neighbor not in dist:
                dist[neighbor] = dist[node] + 1
                queue.append(neighbor)
    return dist


def dijkstra(graph: Graph, source: Any) -> dict:
    """
    Shortest-path distances (by total edge weight) from *source*.

    Returns ``{node: distance}``; unreachable nodes are omitted.
    *source* maps to 0.0.
    """
    dist: dict = {source: 0.0}
    # Min-heap entries: (distance, counter, node)
    # The counter breaks ties deterministically so nodes without a natural
    # ordering don't cause TypeError.
    counter = 0
    heap = [(0.0, counter, source)]
    while heap:
        d, _, node = heapq.heappop(heap)
        if d > dist.get(node, float("inf")):
            continue
        for neighbor, weight in graph.neighbors(node):
            nd = d + weight
            if nd < dist.get(neighbor, float("inf")):
                dist[neighbor] = nd
                counter += 1
                heapq.heappush(heap, (nd, counter, neighbor))
    return dist


def connected_components(graph: Graph) -> list:
    """
    For **undirected** graphs only.

    Returns a list of sets, where each set contains the nodes of one
    connected component.
    """
    visited: set = set()
    components: list = []
    for node in graph.nodes():
        if node not in visited:
            # BFS to find all nodes in this component
            component: set = set()
            queue: deque = deque([node])
            visited.add(node)
            while queue:
                current = queue.popleft()
                component.add(current)
                for neighbor, _weight in graph.neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)
    return components
