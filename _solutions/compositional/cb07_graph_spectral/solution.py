"""Gold reference for compositional/cb07_graph_spectral — Spectral Partition.

Composes networkx (graph + combinatorial Laplacian), scipy.linalg.eigh
(symmetric eigendecomposition) and numpy (array work) to spectrally partition
an undirected weighted graph via its Fiedler vector.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import scipy.linalg as sla

# Threshold below which an eigenvalue is treated as zero.
_ZERO_TOL = 1e-8


def spectral_partition(edges: list[tuple], n: int) -> dict:
    """Spectrally partition an undirected weighted graph.

    Parameters
    ----------
    edges : list of (u, v, w)
        Undirected edges with 0 <= u, v < n and positive weight w.
    n : int
        Number of nodes (nodes are 0 .. n-1). Isolated nodes are allowed.

    Returns
    -------
    dict with keys:
      fiedler_value : float
          Second-smallest eigenvalue of L = D - A (the algebraic connectivity).
      partition : list[int]
          Length n; entry i is 0 if Fiedler-vector entry i >= 0 else 1.
      connected : bool
          True iff the second-smallest eigenvalue > 1e-8.
      n_components : int
          Number of eigenvalues < 1e-8 (= number of connected components).

    Raises
    ------
    ValueError
        If n < 1, an edge endpoint is outside [0, n), or a weight is <= 0.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    # Build the graph with ALL n nodes (isolated nodes preserved).
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for u, v, w in edges:
        if not (0 <= u < n) or not (0 <= v < n):
            raise ValueError(
                f"edge endpoint out of range: ({u}, {v}) not within [0, {n})"
            )
        if w <= 0:
            raise ValueError(f"edge weight must be positive, got {w}")
        G.add_edge(u, v, weight=float(w))

    # Combinatorial Laplacian L = D - A as a dense array with a FIXED node order.
    L = nx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray().astype(float)

    # Symmetric eigendecomposition, ascending eigenvalues.
    eigvals, eigvecs = sla.eigh(L)
    order = np.argsort(eigvals)
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    # Number of (near-)zero eigenvalues = number of connected components.
    n_components = int(np.sum(eigvals < _ZERO_TOL))

    # Fiedler value/vector: the SECOND-smallest eigenvalue and its eigenvector.
    fiedler_value = float(eigvals[1])
    fiedler_vec = eigvecs[:, 1]

    partition = [0 if val >= 0 else 1 for val in fiedler_vec]
    connected = bool(fiedler_value > _ZERO_TOL)

    return {
        "fiedler_value": fiedler_value,
        "partition": partition,
        "connected": connected,
        "n_components": n_components,
    }
