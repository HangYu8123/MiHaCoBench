"""Gold reference for competitive/cp07_path_xor_sum.

Sum, over all unordered pairs of distinct nodes (a, b) in a TREE, of the XOR of
the edge weights on the unique a->b path, taken modulo 1_000_000_007.

Key observation
---------------
Root the tree at any node and let ``xr[v]`` be the XOR of the edge weights on the
path from the root to ``v`` (``xr[root] = 0``). For any two nodes a and b, the
path between them is (root->a) XOR (root->b): every edge on the shared portion
(root -> LCA) appears in both root-paths and cancels under XOR, leaving exactly
the edges on the a<->b path. Therefore::

    pathxor(a, b) == xr[a] ^ xr[b]

So the answer is ``sum over all pairs (a < b) of (xr[a] ^ xr[b])``. Summing a XOR
over pairs decomposes per bit: for bit ``b``, two values contribute ``2**b`` to
their XOR iff exactly one of them has bit ``b`` set. If ``c`` of the ``n`` values
have bit ``b`` set, the number of such pairs is ``c * (n - c)``, so::

    answer = sum_{b=0}^{29} c_b * (n - c_b) * 2**b   (mod M)

Edge weights satisfy ``0 <= w < 2**30``, so 30 bits suffice.

Complexity
----------
* Time:  O(n * 30) = O(n log V) — one pass to build ``xr`` (iterative BFS over the
  n-1 edges) plus a 30-bit popcount sweep.
* Space: O(n) for the adjacency lists, ``xr`` array and the BFS frontier.

The root-to-node XOR is computed with an ITERATIVE traversal: a recursive DFS
would overflow Python's recursion limit on a degenerate (path-shaped) tree of
n = 200_000 nodes.
"""
from __future__ import annotations

from collections import deque

MOD = 1_000_000_007
_BITS = 30  # edge weights are in [0, 2**30)


def sum_path_xor(n: int, edges: list[tuple[int, int, int]]) -> int:
    """Return sum over all unordered distinct node pairs of the path-XOR, mod 1e9+7.

    Parameters
    ----------
    n : int
        Number of nodes, labelled 0..n-1. The graph is a tree, so there are
        exactly n-1 edges.
    edges : list[tuple[int, int, int]]
        Each ``(u, v, w)`` is an undirected edge between nodes u and v with weight
        ``0 <= w < 2**30``.

    Returns
    -------
    int
        ``sum_{a<b} (pathxor(a, b)) mod 1_000_000_007``, where ``pathxor(a, b)`` is
        the XOR of the edge weights on the unique path from a to b. ``0`` when
        ``n <= 1``.
    """
    if n <= 1:
        return 0

    # Adjacency list: adj[u] = list of (neighbour, weight).
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    # xr[v] = XOR of edge weights from the root (node 0) to v, via iterative BFS.
    # The tree is connected with exactly n-1 edges, so a single BFS from node 0
    # reaches every node.
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

    # Per-bit pair count: bit b contributes 2**b for every pair whose two xr values
    # differ in bit b, i.e. (#set in bit b) * (#unset in bit b) pairs.
    ans = 0
    for b in range(_BITS):
        mask = 1 << b
        cnt_set = 0
        for value in xr:
            if value & mask:
                cnt_set += 1
        cnt_unset = n - cnt_set
        ans = (ans + (cnt_set * cnt_unset % MOD) * (mask % MOD)) % MOD

    return ans % MOD
