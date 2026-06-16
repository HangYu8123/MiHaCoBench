"""ranking.py — PageRank and degree centrality."""

import numpy as np


def pagerank(graph, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-9) -> dict:
    """
    Compute PageRank using power iteration.

    PR(v) = (1 - d) / N + d * sum(PR(u) / out_degree(u)) for each in-neighbour u

    Returns {node: pagerank_value} for every node.
    Values sum to ~1.0 (within 1e-6).
    """
    nodes = list(graph._nodes)
    N = len(nodes)

    if N == 0:
        return {}

    if N == 1:
        return {nodes[0]: 1.0}

    idx = {n: i for i, n in enumerate(nodes)}

    # Build transition matrix M: M[i, j] = probability of going from j to i
    M = np.zeros((N, N), dtype=np.float64)

    dangling = []  # nodes with no outgoing edges

    for node in nodes:
        j = idx[node]
        # For directed graphs, out-edges are stored in _adj[node]
        # For undirected graphs, same _adj[node] stores neighbors
        out_neighbors = list(graph._adj[node].items())
        out_degree = len(out_neighbors)

        if out_degree == 0:
            dangling.append(j)
        else:
            for neighbor, _weight in out_neighbors:
                i = idx[neighbor]
                M[i, j] += 1.0 / out_degree

    # Power iteration
    r = np.ones(N, dtype=np.float64) / N
    dangling_weights = np.ones(N, dtype=np.float64) / N  # uniform dangling distribution

    for _ in range(max_iter):
        # Handle dangling nodes: their mass is redistributed uniformly
        dangling_sum = sum(r[j] for j in dangling)

        r_new = (1.0 - damping) / N + damping * (M @ r + dangling_sum * dangling_weights)

        # Check convergence
        if np.abs(r_new - r).sum() < tol:
            r = r_new
            break
        r = r_new

    return {nodes[i]: float(r[i]) for i in range(N)}


def degree_centrality(graph) -> dict:
    """
    Compute degree centrality for each node.

    For undirected: degree / (N - 1)
    For directed: (in_degree + out_degree) / (N - 1)
    For N <= 1: {node: 0.0} for all nodes.

    Self-loops: for directed graphs, a self-loop contributes 1 to out-degree
    and 1 to in-degree, so +2 to total degree.
    """
    N = graph.num_nodes

    if N <= 1:
        return {n: 0.0 for n in graph._nodes}

    result = {}

    if not graph._directed:
        # Undirected: degree is number of neighbors (self-loop counts once)
        for node in graph._nodes:
            deg = len(graph._adj[node])
            result[node] = deg / (N - 1)
    else:
        # Directed: total degree = out_degree + in_degree
        # out-degree from _adj[node]
        # in-degree: count how many nodes have this node as neighbor

        # Build in-degree map
        in_degree = {n: 0 for n in graph._nodes}
        for node in graph._nodes:
            for neighbor in graph._adj[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        for node in graph._nodes:
            out_deg = len(graph._adj[node])
            in_deg = in_degree.get(node, 0)
            result[node] = (out_deg + in_deg) / (N - 1)

    return result
