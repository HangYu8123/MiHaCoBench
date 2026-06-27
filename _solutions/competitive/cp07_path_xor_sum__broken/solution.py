"""Broken reference for competitive/cp07_path_xor_sum.

PLANTED DEFECT (subtle misobservation): for each bit b, this counts pairs that
lie WITHIN the same bit-group — C(cnt_set, 2) + C(cnt_unset, 2) — instead of the
cross pairs cnt_set * cnt_unset. XOR's bit b is set exactly when the two operands
DIFFER in bit b, so the correct per-bit pair count is the CROSS product
cnt_set * cnt_unset, not the within-group count. Everything else (the xr-prefix
observation, the iterative BFS, the modulus, the 30-bit sweep) is identical, so
this is correct only in degenerate cases and wrong in general.
"""
from __future__ import annotations

from collections import deque

MOD = 1_000_000_007
_BITS = 30  # edge weights are in [0, 2**30)


def sum_path_xor(n: int, edges: list[tuple[int, int, int]]) -> int:
    """Return sum over all unordered distinct node pairs of the path-XOR, mod 1e9+7.

    BROKEN: uses within-group pair counts (C(set,2)+C(unset,2)) per bit instead of
    the cross product set*unset, so it returns a wrong sum in general.
    """
    if n <= 1:
        return 0

    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    xr = [0] * n
    visited = [False] * n
    visited[0] = True
    frontier = deque([0])
    while frontier:
        u = frontier.popleft()
        xu = xr[u]
        for v, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                xr[v] = xu ^ w
                frontier.append(v)

    ans = 0
    for b in range(_BITS):
        mask = 1 << b
        cnt_set = 0
        for value in xr:
            if value & mask:
                cnt_set += 1
        cnt_unset = n - cnt_set
        # BUG: within-group pairs instead of the cross product cnt_set * cnt_unset.
        pairs = cnt_set * (cnt_set - 1) // 2 + cnt_unset * (cnt_unset - 1) // 2
        ans = (ans + (pairs % MOD) * (mask % MOD)) % MOD

    return ans % MOD
