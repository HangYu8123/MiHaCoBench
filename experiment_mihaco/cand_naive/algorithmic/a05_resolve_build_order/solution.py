import heapq
from collections import defaultdict


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    """
    Returns the lexicographically-smallest valid topological ordering of n tasks
    (labelled 0..n-1) given dependency edges using Kahn's algorithm with a min-heap.

    Raises ValueError if the graph contains a cycle.
    """
    # Build adjacency list and in-degree count
    # Use a set of edges to handle duplicates
    adj = defaultdict(list)
    in_degree = [0] * n
    seen_edges = set()

    for a, b in deps:
        if (a, b) not in seen_edges:
            seen_edges.add((a, b))
            adj[a].append(b)
            in_degree[b] += 1

    # Initialize min-heap with all nodes that have in-degree 0
    heap = []
    for i in range(n):
        if in_degree[i] == 0:
            heapq.heappush(heap, i)

    result = []
    while heap:
        # Pick the smallest available task
        task = heapq.heappop(heap)
        result.append(task)

        # Reduce in-degree of neighbors
        for neighbor in adj[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    if len(result) != n:
        raise ValueError("Cycle detected in dependency graph; topological sort is impossible.")

    return result
