"""
Sum of weighted distances in a tree — O(n) two-pass rerooting DP.

Algorithm:
  Pass 1 (post-order from root 0):
    - subtree_dist[v] = sum of weighted distances from v to all nodes in its subtree
    - subtree_size[v] = number of nodes in v's subtree

  Pass 2 (pre-order from root 0):
    - res[v] = sum of weighted distances from v to ALL other nodes
    - When we move the root from parent p to child c via edge weight w:
        res[c] = res[p]
                 - subtree_size[c] * w        (nodes in c's subtree get w closer)
                 + (n - subtree_size[c]) * w  (nodes outside c's subtree get w farther)
"""


def sum_of_distances(n: int, edges: list[tuple]) -> list[int]:
    """Return res where res[i] = sum of weighted distances from node i to ALL other nodes."""
    if n == 1:
        return [0]

    # Build adjacency list: adj[u] = list of (v, w)
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    subtree_size = [1] * n
    subtree_dist = [0] * n  # sum of distances from node v to all nodes in its subtree

    parent = [-1] * n
    parent_weight = [0] * n
    order = []  # BFS/DFS order for post-order processing

    # Iterative DFS to compute post-order
    stack = [0]
    visited = [False] * n
    visited[0] = True

    while stack:
        v = stack.pop()
        order.append(v)
        for u, w in adj[v]:
            if not visited[u]:
                visited[u] = True
                parent[u] = v
                parent_weight[u] = w
                stack.append(u)

    # Pass 1: process in reverse order (post-order)
    for v in reversed(order):
        p = parent[v]
        if p != -1:
            w = parent_weight[v]
            # v's contribution to p's subtree:
            # all subtree_size[v] nodes are w farther than they were relative to v
            subtree_dist[p] += subtree_dist[v] + subtree_size[v] * w
            subtree_size[p] += subtree_size[v]

    # Pass 2: rerooting — process in BFS order (pre-order)
    res = [0] * n
    res[0] = subtree_dist[0]

    for v in order:
        for u, w in adj[v]:
            if parent[u] == v:
                # u is a child of v
                # When moving root from v to u:
                #   nodes in u's subtree: each gains -w (distance decreases by w)
                #   nodes outside u's subtree: each gains +w (distance increases by w)
                res[u] = res[v] - subtree_size[u] * w + (n - subtree_size[u]) * w

    return res
