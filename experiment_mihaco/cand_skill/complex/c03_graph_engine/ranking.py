"""
ranking.py — Graph ranking algorithms: PageRank and degree centrality.
"""

import numpy as np


def pagerank(graph, damping: float = 0.85, max_iter: int = 100,
             tol: float = 1e-9) -> dict:
    """Compute PageRank via power iteration.

    Returns {node: float} where all values sum to approximately 1.0.
    Uses sorted node ordering for determinism regardless of dict insertion
    order (safe even without PYTHONHASHSEED=0).

    Edge cases:
    - N=0: return {}
    - N=1: return {node: 1.0}
    """
    nodes = sorted(graph._adj.keys(), key=lambda x: (str(type(x).__name__), x)
                   if not isinstance(x, (int, float, str)) else (str(type(x).__name__), x))
    N = len(nodes)

    if N == 0:
        return {}
    if N == 1:
        return {nodes[0]: 1.0}

    # Build node -> index mapping
    idx = {n: i for i, n in enumerate(nodes)}

    # Build column-stochastic transition matrix T (shape N x N)
    # T[i, j] = probability of going from node j to node i
    T = np.zeros((N, N), dtype=float)

    for j, node in enumerate(nodes):
        neighbors = list(graph._adj[node].items())
        if not neighbors:
            # Dangling node: distribute uniformly
            T[:, j] = 1.0 / N
        else:
            # Weight-normalized column (not just counting edges — use uniform
            # if weights are present; per standard PageRank we count links,
            # but the spec says "PR(u)/out_degree(u)" so we use uniform
            # distribution over out-neighbors regardless of weight).
            out_degree = len(neighbors)
            for neighbor, _weight in neighbors:
                if neighbor in idx:
                    T[idx[neighbor], j] += 1.0 / out_degree

    # Power iteration
    pr = np.full(N, 1.0 / N, dtype=float)
    teleport = (1.0 - damping) / N

    for _ in range(max_iter):
        pr_new = teleport + damping * (T @ pr)
        if np.linalg.norm(pr_new - pr) < tol:
            pr = pr_new
            break
        pr = pr_new

    return {node: float(pr[idx[node]]) for node in nodes}


def degree_centrality(graph) -> dict:
    """Compute degree centrality for each node.

    For undirected graphs: degree / (N-1).
    For directed graphs: (in_degree + out_degree) / (N-1).
    For N <= 1: return {node: 0.0} for all nodes.
    """
    N = graph.num_nodes
    result = {}

    if N <= 1:
        return {n: 0.0 for n in graph._adj}

    denominator = float(N - 1)

    # Compute out-degrees from _adj
    out_deg = {n: len(graph._adj[n]) for n in graph._adj}

    if graph._directed:
        # Accumulate in-degree by scanning all edges
        in_deg = {n: 0 for n in graph._adj}
        for u, neighbors in graph._adj.items():
            for v in neighbors:
                if v in in_deg:
                    in_deg[v] += 1
                # If v is not in _adj (shouldn't happen with proper add_edge)
                # we skip; add_edge always calls add_node for both endpoints.

        for n in graph._adj:
            total = out_deg[n] + in_deg[n]
            result[n] = total / denominator
    else:
        # For undirected, degree = number of distinct neighbors
        # (self-loop counts as 1 in _adj[n][n], so it adds 1 to degree)
        for n in graph._adj:
            result[n] = out_deg[n] / denominator

    return result
