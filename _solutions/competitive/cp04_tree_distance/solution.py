"""Gold reference for competitive/cp04_tree_distance.

Computes sum of weighted distances from every node to all other nodes in O(n)
using the classic two-pass rerooting (re-rooting) tree DP.

Algorithm outline (ITERATIVE DFS to avoid Python recursion-limit on deep trees):
  Pass 1 (bottom-up from leaves to root, DFS post-order):
    - sub_size[v] = number of nodes in the subtree rooted at v (when rooted at 0)
    - down[v]     = sum of weighted distances from v to all nodes in its subtree

  Pass 2 (top-down from root to leaves, DFS pre-order):
    - ans[v]      = total sum of weighted distances from v to ALL n nodes
    Using the rerooting identity: when edge (parent -> child, weight w) is
    considered, moving the "root" from parent to child:
      ans[child] = ans[parent]
                 - sub_size[child] * w   (nodes in child's subtree get w closer)
                 + (n - sub_size[child]) * w  (remaining nodes get w farther)
"""
from __future__ import annotations

from collections import deque


def sum_of_distances(n: int, edges: list[tuple]) -> list[int]:
    """Return res where res[i] = sum of weighted distances from node i to all others.

    Parameters
    ----------
    n : int
        Number of nodes (0-indexed).
    edges : list[tuple]
        n-1 undirected weighted edges as (u, v, w).

    Returns
    -------
    list[int]
        Length-n list of total weighted distances.
    """
    if n == 1:
        return [0]

    # Build adjacency list: adj[u] = [(v, w), ...]
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    # ---------- Pass 1: bottom-up (post-order iterative DFS from root=0) ----------
    parent = [-1] * n
    parent_w = [0] * n          # weight of edge to parent
    order: list[int] = []       # post-order traversal order
    sub_size = [1] * n          # subtree sizes
    down = [0] * n              # sum of weighted distances to subtree nodes

    # Iterative DFS using an explicit stack (avoids recursion limit)
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                parent_w[v] = w
                stack.append(v)

    # Process in reverse order (children before parents)
    for u in reversed(order):
        p = parent[u]
        if p != -1:
            w = parent_w[u]
            sub_size[p] += sub_size[u]
            down[p] += down[u] + sub_size[u] * w

    # ---------- Pass 2: top-down (re-rooting, pre-order) ----------
    ans = [0] * n
    ans[0] = down[0]            # root's answer is the sum of all downward distances

    # Process in DFS pre-order (parent before children)
    for u in order:
        for v, w in adj[u]:
            if v == parent[u]:
                continue        # skip the edge back to parent
            # Rerooting identity:
            # ans[v] = ans[u] + (n - sub_size[v]) * w - sub_size[v] * w
            ans[v] = ans[u] + (n - 2 * sub_size[v]) * w

    return ans
