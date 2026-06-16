"""Deliberately-broken reference for competitive/cp04_tree_distance.

Planted defect: naive O(n^2) — runs a BFS/Dijkstra from every node independently.

This is CORRECT for all small test cases (produces identical answers to the gold),
but TIMES OUT on the hard complexity gate (n=200000, timeout=15s) because
O(n^2) dominates: 200000^2 / 2 ≈ 2 × 10^10 operations takes many minutes.

The defect is LOCALIZED: all correctness tests (small n) PASS; only the
adversarial time-gate test FAILS.
"""
from __future__ import annotations

import heapq


def sum_of_distances(n: int, edges: list[tuple]) -> list[int]:
    """Return res where res[i] = sum of weighted distances from node i to all others.

    BUG: Runs Dijkstra from each node — O(n^2 log n) total. Correct on small
    inputs but times out on large trees (n=200000, timeout=15s).
    """
    if n == 1:
        return [0]

    # Build adjacency list
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    def dijkstra_sum(src: int) -> int:
        """Run Dijkstra from src and return sum of all distances."""
        dist = [float("inf")] * n
        dist[src] = 0
        heap = [(0, src)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        return sum(dist)

    # O(n) calls to Dijkstra — O(n^2 log n) total
    return [dijkstra_sum(i) for i in range(n)]
