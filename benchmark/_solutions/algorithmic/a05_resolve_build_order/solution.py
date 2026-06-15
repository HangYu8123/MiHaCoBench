"""Gold reference for algorithmic/a05_resolve_build_order.

Kahn's algorithm with a min-heap for lexicographically-smallest topological sort.
Time complexity: O((V + E) log V) — each node and edge is processed once;
the heap operations are O(log V) per node, which is O(V log V + E) overall.
This satisfies the O(V + E) spirit (the log V factor from the heap is the
standard accepted cost for the lex-smallest variant).
"""
from __future__ import annotations

import heapq
from collections import defaultdict


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    """Return the lexicographically-smallest topological ordering of tasks 0..n-1.

    Parameters
    ----------
    n:
        Number of tasks (labelled 0 through n-1).
    deps:
        Dependency pairs (a, b) meaning task a must precede task b.
        Duplicate edges and self-loops are handled correctly.

    Returns
    -------
    list[int]
        A valid topological ordering with lex-smallest tie-breaking.

    Raises
    ------
    ValueError
        If the dependency graph contains a cycle (including self-loops).
    """
    # Build adjacency list and in-degree table, ignoring duplicate edges.
    in_degree: list[int] = [0] * n
    adj: list[list[int]] = [[] for _ in range(n)]
    seen_edges: set[tuple[int, int]] = set()

    for a, b in deps:
        if (a, b) in seen_edges:
            continue
        seen_edges.add((a, b))
        if a == b:
            # Self-loop — immediately a cycle.
            raise ValueError(f"Cycle detected: self-loop on task {a}")
        adj[a].append(b)
        in_degree[b] += 1

    # Kahn's algorithm: start with all zero-in-degree nodes in a min-heap.
    heap: list[int] = [i for i in range(n) if in_degree[i] == 0]
    heapq.heapify(heap)

    order: list[int] = []
    while heap:
        node = heapq.heappop(heap)
        order.append(node)
        for neighbour in adj[node]:
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                heapq.heappush(heap, neighbour)

    if len(order) != n:
        raise ValueError(
            f"Cycle detected: only {len(order)} of {n} tasks could be ordered."
        )

    return order
