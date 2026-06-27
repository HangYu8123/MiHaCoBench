"""Graph traversal algorithms: BFS, Dijkstra, connected components."""

from collections import deque
import heapq


def bfs(graph, source) -> dict:
    """Breadth-first traversal from source.

    Returns a dict mapping each reachable node (including source)
    to its hop distance (number of edges). source maps to 0.
    Unreachable nodes are omitted.
    """
    distances = {source: 0}
    queue = deque([source])

    while queue:
        node = queue.popleft()
        for neighbor, _ in graph.neighbors(node):
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)

    return distances


def dijkstra(graph, source) -> dict:
    """Shortest-path distances (by edge weight sum) from source to every reachable node.

    Returns {node: distance}. source maps to 0.0. Unreachable nodes are omitted.
    """
    distances = {source: 0.0}
    # priority queue: (distance, node)
    heap = [(0.0, source)]

    while heap:
        dist, node = heapq.heappop(heap)

        # Skip if we already found a shorter path
        if dist > distances.get(node, float('inf')):
            continue

        for neighbor, weight in graph.neighbors(node):
            new_dist = dist + weight
            if new_dist < distances.get(neighbor, float('inf')):
                distances[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return distances


def connected_components(graph) -> list:
    """For undirected graphs only.

    Returns a list of sets, where each set contains the nodes
    of one connected component.
    """
    nodes = set(graph.nodes())
    visited = set()
    components = []

    for start_node in nodes:
        if start_node in visited:
            continue

        # BFS to find all nodes in this component
        component = set()
        queue = deque([start_node])
        component.add(start_node)
        visited.add(start_node)

        while queue:
            node = queue.popleft()
            for neighbor, _ in graph.neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)

        components.append(component)

    return components
