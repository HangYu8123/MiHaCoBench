"""Node-ranking algorithms: PageRank and degree centrality."""

import numpy as np


def pagerank(graph, damping: float = 0.85, max_iter: int = 100,
             tol: float = 1e-9) -> dict:
    """Compute PageRank via power iteration.

    Returns a dict {node: float} for every node in the graph.
    Values sum to approximately 1.0.
    """
    N = graph.num_nodes
    if N == 0:
        return {}

    # Deterministic node ordering (works for mixed types via repr fallback)
    nodes = sorted(graph._adj.keys(), key=repr)
    idx = {n: i for i, n in enumerate(nodes)}

    # Out-degree array (self-loops count toward out-degree)
    out_deg = np.array(
        [sum(1 for _ in graph.neighbors(n)) for n in nodes],
        dtype=float,
    )

    dangling_mask = (out_deg == 0)

    pr = np.ones(N) / N

    for _ in range(max_iter):
        new_pr = np.zeros(N)

        # Dangling-node rank is distributed uniformly
        dangling_sum = pr[dangling_mask].sum()

        # Accumulate contributions from out-edges
        for u_idx, u in enumerate(nodes):
            if out_deg[u_idx] == 0:
                continue
            contrib = pr[u_idx] / out_deg[u_idx]
            for v, _ in graph.neighbors(u):
                new_pr[idx[v]] += contrib

        new_pr = (1.0 - damping) / N + damping * (new_pr + dangling_sum / N)

        if np.sum(np.abs(new_pr - pr)) < tol:
            pr = new_pr
            break
        pr = new_pr

    return {nodes[i]: float(pr[i]) for i in range(N)}


def degree_centrality(graph) -> dict:
    """Return {node: degree / (N-1)}.

    For directed graphs, degree = in-degree + out-degree.
    For undirected graphs, each edge already appears in both adj-lists so
    len(neighbors(n)) gives the correct degree directly.
    For N <= 1, every node maps to 0.0.
    """
    N = graph.num_nodes
    if N <= 1:
        return {n: 0.0 for n in graph._adj}

    denom = float(N - 1)

    if graph._directed:
        # Out-degree from adjacency dict
        out_deg = {n: sum(1 for _ in graph.neighbors(n)) for n in graph._adj}
        # In-degree by scanning all neighbor lists
        in_deg = {n: 0 for n in graph._adj}
        for u in graph._adj:
            for v, _ in graph.neighbors(u):
                in_deg[v] += 1
        return {n: (out_deg[n] + in_deg[n]) / denom for n in graph._adj}
    else:
        # Undirected: neighbors already stores both directions
        return {
            n: len(list(graph.neighbors(n))) / denom
            for n in graph._adj
        }
