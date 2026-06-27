"""Graph traversal algorithms."""

from collections import deque
import heapq


def bfs(graph, source) -> dict:
    """Breadth-first traversal from *source*.

    Returns a dict mapping each reachable node (including source) to its
    hop distance (number of edges).  Unreachable nodes are omitted.
    """
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for nbr, _ in graph.neighbors(node):
            if nbr not in dist:
                dist[nbr] = dist[node] + 1
                queue.append(nbr)
    return dist


def dijkstra(graph, source) -> dict:
    """Shortest-path distances (by edge weight sum) from *source*.

    Returns {node: distance}.  Unreachable nodes are omitted.
    """
    dist = {source: 0.0}
    heap = [(0.0, source)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist[node]:
            continue
        for nbr, w in graph.neighbors(node):
            nd = d + w
            if nbr not in dist or nd < dist[nbr]:
                dist[nbr] = nd
                heapq.heappush(heap, (nd, nbr))
    return dist


def connected_components(graph) -> list:
    """Return connected components of an *undirected* graph.

    Returns a list of sets; each set contains the nodes of one component.
    """
    visited = set()
    components = []
    for start in graph._adj:
        if start in visited:
            continue
        # BFS flood-fill
        component = set()
        queue = deque([start])
        visited.add(start)
        while queue:
            node = queue.popleft()
            component.add(node)
            for nbr, _ in graph.neighbors(node):
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        components.append(component)
    return components
