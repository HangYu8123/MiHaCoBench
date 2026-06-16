"""
ranking.py — PageRank and degree centrality.
"""

import numpy as np


def pagerank(
    graph,
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-9,
) -> dict:
    """Compute the PageRank of every node using power iteration.

    The returned dict contains every node in the graph and values sum to
    approximately 1.0.

    Algorithm (column-stochastic formulation with dangling-node handling):
        PR(v) = (1-d)/N + d * (dangling_sum/N + Σ PR(u)/out_degree(u))
    where the sum is over all in-neighbours u of v.
    """
    nodes = list(graph._adj.keys())
    N = len(nodes)

    if N == 0:
        return {}

    if N == 1:
        return {nodes[0]: 1.0}

    # Map each node to a stable integer index (insertion order, deterministic
    # under Python 3.7+ with PYTHONHASHSEED=0).
    idx = {n: i for i, n in enumerate(nodes)}

    # Build the column-stochastic transition matrix M (shape N×N).
    # M[i][j] = 1/out_degree(j)  if edge j→i exists, else 0.
    # Dangling nodes (out_degree == 0) get no column entries; they are
    # handled separately via dangling_sum redistribution.
    out_degree = np.zeros(N, dtype=float)
    for node in nodes:
        out_degree[idx[node]] = len(graph._adj[node])

    is_dangling = out_degree == 0.0

    # Fill transition matrix column by column.
    M = np.zeros((N, N), dtype=float)
    for node in nodes:
        j = idx[node]
        od = out_degree[j]
        if od == 0:
            continue  # dangling — handled via dangling_sum
        for nbr, _weight in graph._adj[node].items():
            i = idx[nbr]
            M[i][j] = 1.0 / od

    # Power iteration
    r = np.full(N, 1.0 / N, dtype=float)
    d = damping

    for _ in range(max_iter):
        dangling_sum = float(np.sum(r[is_dangling]))
        r_new = (1.0 - d) / N + d * (dangling_sum / N + M @ r)
        if np.sum(np.abs(r_new - r)) < tol:
            r = r_new
            break
        r = r_new

    return {node: float(r[idx[node]]) for node in nodes}


def degree_centrality(graph) -> dict:
    """Return {node: degree / (N-1)}.

    For directed graphs, use the total degree (in + out).
    For N <= 1, return {node: 0.0} for all nodes.
    Every node in the graph appears in the result.
    """
    nodes = list(graph._adj.keys())
    N = len(nodes)

    if N <= 1:
        return {n: 0.0 for n in nodes}

    if graph.directed:
        # out-degree from adjacency dict; in-degree by scanning all lists
        out_deg = {n: len(graph._adj[n]) for n in nodes}
        in_deg = {n: 0 for n in nodes}
        for node in nodes:
            for nbr in graph._adj[node]:
                in_deg[nbr] = in_deg.get(nbr, 0) + 1

        return {
            n: (out_deg[n] + in_deg[n]) / (N - 1)
            for n in nodes
        }
    else:
        # Undirected: degree = number of distinct neighbours
        # (self-loops appear once in _adj[n] keyed by n itself)
        return {n: len(graph._adj[n]) / (N - 1) for n in nodes}
