import heapq
from collections import defaultdict


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    """Return the lexicographically-smallest topological ordering of n tasks.

    Parameters
    ----------
    n : int
        Number of tasks, labelled 0 through n-1.
    deps : list[tuple[int, int]]
        Dependency edges. (a, b) means task a must complete before task b.
        Duplicate edges are allowed and treated as a single dependency.
        Self-loops (a, a) indicate a cycle.

    Returns
    -------
    list[int]
        Valid topological ordering of all n tasks.

    Raises
    ------
    ValueError
        If the dependency graph contains a cycle.
    """
    if n == 0:
        return []

    # Deduplicate edges (handles duplicate edges and self-loops transparently)
    unique_deps = set(deps)

    # Build adjacency list and in-degree array
    adj = defaultdict(list)
    in_degree = [0] * n

    for a, b in unique_deps:
        adj[a].append(b)
        in_degree[b] += 1

    # Initialize min-heap with all zero-in-degree nodes
    heap = []
    for node in range(n):
        if in_degree[node] == 0:
            heapq.heappush(heap, node)

    result = []

    # Kahn's algorithm with min-heap for lexicographically-smallest ordering
    while heap:
        node = heapq.heappop(heap)
        result.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    if len(result) < n:
        raise ValueError("cycle detected: topological sort is impossible")

    return result
