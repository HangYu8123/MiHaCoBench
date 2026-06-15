"""Node ranking algorithms for c03_graph_engine.

Implements:
    pagerank          — power-iteration PageRank
    degree_centrality — normalized degree centrality
"""
from __future__ import annotations

from typing import Any

import numpy as np

from structures import Graph


def pagerank(
    graph: Graph,
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-9,
) -> dict[Any, float]:
    """Compute PageRank via power iteration.

    The standard formulation used here:

        PR(v) = (1 - d) / N  +  d * Σ_{u: u→v}  PR(u) / out_degree(u)

    where *d* is the damping factor and *N* is the number of nodes.

    Dangling nodes (out-degree 0) distribute their rank equally to all nodes
    (the "dangling node" fix, matching networkx's default behaviour).

    Parameters
    ----------
    graph:
        Directed or undirected ``Graph``.
    damping:
        Damping factor (default 0.85).
    max_iter:
        Maximum number of power-iteration steps.
    tol:
        L1-norm convergence threshold.

    Returns
    -------
    dict
        ``{node: rank}`` for every node; values sum to approximately 1.0.
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    if n == 0:
        return {}

    # Map nodes to integer indices
    idx: dict[Any, int] = {node: i for i, node in enumerate(nodes)}

    # Build column-stochastic transition matrix (as numpy array)
    # M[j, i] = w_{ij} / out_sum_i  (probability of going from i to j)
    M = np.zeros((n, n), dtype=float)
    dangling: list[int] = []

    for u in nodes:
        i = idx[u]
        nbrs = list(graph.neighbors(u))
        if not nbrs:
            dangling.append(i)
            continue
        out_sum = sum(w for _, w in nbrs)
        for v, w in nbrs:
            j = idx[v]
            M[j, i] += w / out_sum  # column i, row j

    # Start with uniform distribution
    pr = np.full(n, 1.0 / n, dtype=float)
    base = np.full(n, (1.0 - damping) / n, dtype=float)

    for _ in range(max_iter):
        # Handle dangling nodes: redistribute their rank uniformly
        dangling_sum = pr[dangling].sum() if dangling else 0.0
        dangling_contrib = damping * dangling_sum / n

        new_pr = base + damping * M.dot(pr) + dangling_contrib
        # Renormalize to handle floating-point drift
        new_pr /= new_pr.sum()

        if np.abs(new_pr - pr).sum() < tol:
            pr = new_pr
            break
        pr = new_pr

    return {node: float(pr[idx[node]]) for node in nodes}


def degree_centrality(graph: Graph) -> dict[Any, float]:
    """Normalized degree centrality for every node.

    For undirected graphs: ``degree(v) / (N - 1)``
    For directed graphs: ``(in_degree(v) + out_degree(v)) / (N - 1)``

    For graphs with ``N <= 1`` every node gets centrality ``0.0``.

    Parameters
    ----------
    graph:
        Directed or undirected ``Graph``.

    Returns
    -------
    dict
        ``{node: centrality}`` for every node in the graph.
    """
    nodes = list(graph.nodes())
    n = len(nodes)

    if n <= 1:
        return {node: 0.0 for node in nodes}

    normalizer = float(n - 1)
    result: dict[Any, float] = {}

    if not graph.is_directed:
        # Undirected: degree = number of neighbours
        for node in nodes:
            degree = len(list(graph.neighbors(node)))
            result[node] = degree / normalizer
    else:
        # Directed: total degree = out-degree + in-degree
        # out-degree: count outgoing edges per node
        out_deg: dict[Any, int] = {node: 0 for node in nodes}
        in_deg: dict[Any, int] = {node: 0 for node in nodes}
        for u in nodes:
            nbrs = list(graph.neighbors(u))
            out_deg[u] = len(nbrs)
            for v, _ in nbrs:
                in_deg[v] = in_deg.get(v, 0) + 1

        for node in nodes:
            total = out_deg[node] + in_deg.get(node, 0)
            result[node] = total / normalizer

    return result
