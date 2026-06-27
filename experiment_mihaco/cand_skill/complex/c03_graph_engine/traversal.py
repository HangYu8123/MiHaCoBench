"""
traversal.py — Graph traversal algorithms: BFS, Dijkstra, connected components.
"""

import collections
import heapq


def bfs(graph, source) -> dict:
    """Breadth-first traversal from source.

    Returns a dict mapping each reachable node (including source) to its hop
    distance (number of edges). Unreachable nodes are omitted.
    """
    if source not in graph._adj:
        return {}

    dist = {source: 0}
    queue = collections.deque([source])

    while queue:
        node = queue.popleft()
        for neighbor, _ in graph.neighbors(node):
            if neighbor not in dist:
                dist[neighbor] = dist[node] + 1
                queue.append(neighbor)

    return dist


def dijkstra(graph, source) -> dict:
    """Shortest-path distances by edge weight from source.

    Returns {node: float_distance}. Source maps to 0.0. Unreachable nodes
    are omitted.
    """
    if source not in graph._adj:
        return {}

    dist = {source: 0.0}
    # heap entries: (distance, node)
    heap = [(0.0, source)]

    while heap:
        d, node = heapq.heappop(heap)
        if d > dist.get(node, float('inf')):
            # Stale entry; skip
            continue
        for neighbor, weight in graph.neighbors(node):
            new_dist = d + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return dist


def connected_components(graph) -> list:
    """Return list of sets of nodes, one per connected component.

    Treats the graph as undirected: builds a symmetric adjacency from
    graph._adj regardless of whether the graph was constructed as directed.
    This is correct for undirected graphs (per spec) and provides a
    well-defined result for directed graphs by treating all edges as
    undirected.
    """
    # Build undirected adjacency: for each directed edge u->v also add v->u
    undirected: dict = {n: set() for n in graph._adj}
    for u, neighbors in graph._adj.items():
        for v in neighbors:
            undirected[u].add(v)
            if v in undirected:
                undirected[v].add(u)
            else:
                # v might not be in undirected if graph is in inconsistent state
                undirected[v] = {u}

    visited: set = set()
    components: list = []

    for start in undirected:
        if start in visited:
            continue
        # BFS to find all nodes in this component
        component: set = set()
        queue = collections.deque([start])
        visited.add(start)
        while queue:
            node = queue.popleft()
            component.add(node)
            for neighbor in undirected[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(component)

    return components
