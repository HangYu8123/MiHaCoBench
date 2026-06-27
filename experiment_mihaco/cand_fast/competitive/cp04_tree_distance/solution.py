from collections import defaultdict


def sum_of_distances(n: int, edges: list[tuple]) -> list[int]:
    """Return res where res[i] = sum of weighted distances from node i to ALL other nodes."""
    if n == 1:
        return [0]

    # Build adjacency list: adj[u] = [(v, w), ...]
    adj = defaultdict(list)
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    # Arrays
    sz = [1] * n       # subtree sizes (rooted at 0)
    down = [0] * n     # sum of weighted distances from v to all nodes in its subtree
    parent = [-1] * n  # parent of each node in the rooted tree
    parent_w = [0] * n # weight of the edge to parent

    # Pass 1: iterative post-order DFS rooted at node 0
    # Build post_order list (children before parents)
    post_order = []
    stack = [(0, -1)]  # (node, parent)
    while stack:
        v, p = stack.pop()
        post_order.append(v)
        parent[v] = p
        for neighbor, w in adj[v]:
            if neighbor != p:
                parent_w[neighbor] = w
                stack.append((neighbor, v))

    # Process in reverse post-order (children before parents)
    for v in reversed(post_order):
        p = parent[v]
        if p == -1:
            continue  # root node, no parent to update
        w = parent_w[v]
        # Accumulate child's contribution into parent
        sz[p] += sz[v]
        down[p] += down[v] + sz[v] * w

    # Pass 2: iterative pre-order top-down (process parents before children)
    res = [0] * n
    res[0] = down[0]  # root sees all nodes

    # post_order is already in pre-order for pass 2 (root first, leaves last)
    for v in post_order:
        p = parent[v]
        if p == -1:
            continue  # root already set
        w = parent_w[v]
        # Moving the "virtual root" from p to v:
        # - sz[v] nodes in v's subtree get closer by w
        # - (n - sz[v]) nodes outside v's subtree get farther by w
        res[v] = res[p] + (n - 2 * sz[v]) * w

    return res
