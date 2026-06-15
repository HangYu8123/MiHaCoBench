"""Deliberately-broken reference for algorithmic/a05_resolve_build_order.

Planted defect: the cycle-detection check is REMOVED.
When a cycle exists, the function silently returns a partial order (missing
nodes that are stuck in the cycle) instead of raising ValueError.
This must fail the cycle-detection tests in the grader.
"""
from __future__ import annotations

import heapq


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    """Return a topological ordering of tasks 0..n-1.

    BUG: does not raise ValueError when a cycle is present — returns a
    truncated list instead.
    """
    in_degree: list[int] = [0] * n
    adj: list[list[int]] = [[] for _ in range(n)]
    seen_edges: set[tuple[int, int]] = set()

    for a, b in deps:
        if (a, b) in seen_edges:
            continue
        seen_edges.add((a, b))
        if a == b:
            # BUG: self-loop is silently ignored instead of raising ValueError
            continue
        adj[a].append(b)
        in_degree[b] += 1

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

    # BUG: missing cycle check — should raise ValueError if len(order) != n
    # Instead, silently return the partial order.
    return order
