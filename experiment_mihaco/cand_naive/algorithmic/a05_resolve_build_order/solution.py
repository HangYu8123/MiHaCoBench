"""
resolve_build_order: Lexicographically-smallest topological sort using Kahn's algorithm with a min-heap.
"""

import heapq
from collections import defaultdict


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    """
    Return the lexicographically-smallest valid topological ordering of n tasks (0..n-1).

    Parameters:
        n: Number of tasks, labelled 0 through n-1.
        deps: Dependency edges. A pair (a, b) means task a must complete before task b.
              May be empty. Self-loops (a, a) are valid inputs and indicate a cycle.

    Returns:
        A list[int] containing a valid topological ordering of all n tasks.

    Raises:
        ValueError: If the dependency graph contains a cycle.
    """
    # Build adjacency list and in-degree counts.
    # Use a set of edges to handle duplicate edges.
    adj = defaultdict(list)
    in_degree = [0] * n
    seen_edges = set()

    for a, b in deps:
        if (a, b) in seen_edges:
            continue
        seen_edges.add((a, b))
        # Self-loop is a cycle
        if a == b:
            raise ValueError(f"Cycle detected: self-loop on task {a}")
        adj[a].append(b)
        in_degree[b] += 1

    # Initialize min-heap with all tasks that have in-degree 0
    heap = []
    for i in range(n):
        if in_degree[i] == 0:
            heapq.heappush(heap, i)

    result = []

    while heap:
        # Always pick the smallest-index task (min-heap ensures this)
        task = heapq.heappop(heap)
        result.append(task)

        # Reduce in-degree of neighbors
        for neighbor in adj[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    # If result doesn't contain all tasks, there's a cycle
    if len(result) != n:
        raise ValueError("Cycle detected: topological sort is impossible")

    return result
