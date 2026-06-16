"""traversal.py — BFS, Dijkstra, and connected components."""

import heapq
from collections import deque


def bfs(graph, source) -> dict:
    """BFS from source. Returns {node: hop_distance} for reachable nodes."""
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for neighbor, _weight in graph.neighbors(node):
            if neighbor not in dist:
                dist[neighbor] = dist[node] + 1
                queue.append(neighbor)
    return dist


def dijkstra(graph, source) -> dict:
    """Dijkstra shortest paths from source. Returns {node: float_distance}."""
    dist = {source: 0.0}
    heap = [(0.0, source)]
    visited = set()

    while heap:
        d, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph.neighbors(node):
            new_dist = d + weight
            if neighbor not in dist or new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return dist


def connected_components(graph) -> list:
    """
    For undirected graphs only.
    Returns a list of sets, each containing nodes of one connected component.
    """
    visited = set()
    components = []

    for node in graph._nodes:
        if node not in visited:
            # BFS to expand this component
            component = set()
            queue = deque([node])
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
