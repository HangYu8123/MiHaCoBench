"""
traversal.py — BFS, Dijkstra, and connected components.
"""

from collections import deque
import heapq


def bfs(graph, source) -> dict:
    """Breadth-first traversal from *source*.

    Returns a dict mapping each reachable node (including source) to its
    hop distance (number of edges).  Source maps to 0.  Unreachable nodes
    are omitted.
    """
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for nbr, _weight in graph.neighbors(node):
            if nbr not in dist:
                dist[nbr] = dist[node] + 1
                queue.append(nbr)
    return dist


def dijkstra(graph, source) -> dict:
    """Shortest-path distances (by edge-weight sum) from *source*.

    Returns {node: distance}.  Source maps to 0.0.  Unreachable nodes are
    omitted.  Uses the weight stored on each edge.
    """
    dist = {source: 0.0}
    visited: set = set()
    heap = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for nbr, weight in graph.neighbors(u):
            new_dist = d + weight
            if nbr not in dist or new_dist < dist[nbr]:
                dist[nbr] = new_dist
                heapq.heappush(heap, (new_dist, nbr))

    return dist


def connected_components(graph) -> list:
    """Connected components for an **undirected** graph.

    Returns a list of sets, where each set contains the nodes of one
    connected component.  Order of the list and order within each set
    are unspecified.

    Since the graph is undirected, both directions are stored in _adj,
    so a plain BFS over _adj[node].keys() is sufficient.
    """
    visited: set = set()
    components: list = []

    for start in graph._adj:
        if start in visited:
            continue
        # BFS to discover this component
        component: set = set()
        queue = deque([start])
        visited.add(start)
        while queue:
            node = queue.popleft()
            component.add(node)
            for nbr in graph._adj[node]:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        components.append(component)

    return components
