import heapq


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    """
    Return the lexicographically-smallest valid topological ordering of n tasks
    using Kahn's algorithm with a min-heap.

    Parameters
    ----------
    n    : Number of tasks, labelled 0 through n-1.
    deps : Dependency edges. (a, b) means task a must complete before task b.
           May contain duplicates and self-loops (which indicate cycles).

    Returns
    -------
    list[int] containing all task labels in topological order.

    Raises
    ------
    ValueError if the dependency graph contains a cycle (including self-loops).
    """
    # Deduplicate edges so duplicate (a, b) pairs are treated as one edge.
    unique_deps = set(deps)

    # Build adjacency list and in-degree array.
    in_degree = [0] * n
    adj = [[] for _ in range(n)]

    for a, b in unique_deps:
        adj[a].append(b)
        in_degree[b] += 1

    # Initialize min-heap with all nodes that have in-degree 0.
    heap = [i for i in range(n) if in_degree[i] == 0]
    heapq.heapify(heap)

    result = []

    while heap:
        # Always pick the smallest-indexed ready node for lexicographic order.
        node = heapq.heappop(heap)
        result.append(node)

        for successor in adj[node]:
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                heapq.heappush(heap, successor)

    # If result does not contain all nodes, a cycle exists.
    if len(result) != n:
        raise ValueError("cycle detected: topological sort is impossible")

    return result
