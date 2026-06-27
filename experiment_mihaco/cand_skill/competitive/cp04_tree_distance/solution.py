def sum_of_distances(n: int, edges: list[tuple]) -> list[int]:
    """Return res where res[i] = sum of weighted distances from node i to ALL other nodes.

    Parameters
    ----------
    n : int
        Number of nodes, 0-indexed: nodes are labelled 0, 1, ..., n-1.
    edges : list[tuple]
        List of n-1 undirected weighted edges, each a tuple (u, v, w) where
        u and v are node indices (0-indexed) and w is a positive integer weight.
        The edges form a valid tree (connected, no cycles).

    Returns
    -------
    list[int]
        A list of n integers: res[i] is the sum of weighted distances from
        node i to every other node j != i.  For n == 1, return [0].
    """
    if n == 1:
        return [0]

    # Build adjacency list: adj[u] = [(v, w), ...]
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    sub_sum = [0] * n   # sum of weighted distances from v to all nodes in v's subtree (rooted at 0)
    sub_cnt = [1] * n   # count of nodes in v's subtree (including v itself)
    res = [0] * n       # final answer for each node

    # Pass 1: bottom-up post-order iterative DFS from root=0
    # Stack entries: (node, parent_node, edge_weight_to_parent, processed)
    # Two-visit pattern:
    #   First pop (processed=False): push (node, par, par_w, True) then push all unvisited children.
    #   Second pop (processed=True): children are done — aggregate subtree into parent.
    stack = [(0, -1, 0, False)]
    while stack:
        node, par, par_w, processed = stack.pop()
        if not processed:
            # Schedule this node for post-order aggregation after its children
            stack.append((node, par, par_w, True))
            for child, w in adj[node]:
                if child != par:
                    stack.append((child, node, w, False))
        else:
            # Post-order: all children of `node` have been fully processed
            if par != -1:
                # node's subtree contributes to parent's subtree stats
                sub_sum[par] += sub_sum[node] + par_w * sub_cnt[node]
                sub_cnt[par] += sub_cnt[node]

    # Pass 2: top-down pre-order iterative DFS from root=0
    # Rerooting formula: when moving the "root perspective" from parent p to child c
    # via edge of weight w:
    #   - sub_cnt[c] nodes each get w closer  -> subtract w * sub_cnt[c]
    #   - (n - sub_cnt[c]) nodes each get w farther -> add w * (n - sub_cnt[c])
    #   => res[c] = res[p] + w * (n - 2 * sub_cnt[c])
    res[0] = sub_sum[0]
    stack = [(0, -1)]
    while stack:
        node, par = stack.pop()
        for child, w in adj[node]:
            if child != par:
                res[child] = res[node] + w * (n - 2 * sub_cnt[child])
                stack.append((child, node))

    return res
