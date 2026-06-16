"""
ranking.py — pagerank, degree_centrality
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
) -> dict:
    """
    Compute PageRank for every node using power iteration.

    Formula per iteration:
        PR(v) = (1-d)/N + d * Σ_{u -> v} PR(u) / out_degree(u)

    Returns a dict ``{node: rank}`` where values sum to approximately 1.0.
    Every node in the graph is included.
    """
    nodes = list(graph.nodes())
    N = len(nodes)
    if N == 0:
        return {}

    # Map nodes to indices
    node_to_idx: dict = {n: i for i, n in enumerate(nodes)}

    # Build out-degree array and transition matrix (column-stochastic)
    # out_degree[i] = number of out-edges from node i (weighted by count, not weight)
    out_degree = np.zeros(N, dtype=float)
    for i, node in enumerate(nodes):
        out_degree[i] = sum(1 for _ in graph.neighbors(node))

    # Build the row-stochastic transition matrix M where M[j, i] = 1/out(i)
    # meaning node i sends its rank equally to all its out-neighbours j.
    # We'll work column-by-column (each column i is the distribution from i).
    M = np.zeros((N, N), dtype=float)
    for i, node in enumerate(nodes):
        if out_degree[i] == 0:
            # Dangling node: distribute rank uniformly to all nodes
            M[:, i] = 1.0 / N
        else:
            for neighbor, _weight in graph.neighbors(node):
                j = node_to_idx[neighbor]
                M[j, i] += 1.0 / out_degree[i]

    # Power iteration
    rank = np.ones(N, dtype=float) / N
    teleport = np.ones(N, dtype=float) / N

    for _ in range(max_iter):
        new_rank = (1.0 - damping) * teleport + damping * M.dot(rank)
        # Normalize to ensure sum = 1 (handles floating-point drift)
        new_rank /= new_rank.sum()
        delta = np.abs(new_rank - rank).sum()
        rank = new_rank
        if delta < tol:
            break

    return {node: float(rank[node_to_idx[node]]) for node in nodes}


def degree_centrality(graph: Graph) -> dict:
    """
    Return ``{node: degree / (N-1)}`` where N is the total number of nodes.

    For directed graphs uses the **total degree** (in + out).
    For N <= 1 returns ``{node: 0.0}`` for all nodes.
    Every node in the graph is included.
    """
    nodes = list(graph.nodes())
    N = len(nodes)
    if N <= 1:
        return {node: 0.0 for node in nodes}

    if not graph.directed:
        # Undirected: degree = number of neighbors (adjacency list length)
        return {
            node: len(dict(graph.neighbors(node))) / (N - 1)
            for node in nodes
        }
    else:
        # Directed: out-degree is easy from adjacency list.
        # In-degree requires counting how many times each node appears as a neighbor.
        in_degree: dict = {node: 0 for node in nodes}
        out_degree: dict = {}
        for node in nodes:
            nbrs = list(graph.neighbors(node))
            out_degree[node] = len(nbrs)
            for neighbor, _weight in nbrs:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        return {
            node: (in_degree[node] + out_degree[node]) / (N - 1)
            for node in nodes
        }
