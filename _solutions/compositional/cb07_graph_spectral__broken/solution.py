"""BROKEN reference for compositional/cb07_graph_spectral — Spectral Partition.

PLANTED DEFECT: uses the SMALLEST eigenvalue (index 0, always ~0) as the
fiedler_value instead of the SECOND-smallest (index 1). Consequently, for a
connected graph fiedler_value is ~0 instead of the true algebraic connectivity,
and `connected` (computed from the same wrong eigenvalue) is always False.

The module still imports and runs cleanly; only the eigenvalue index is wrong.
The exception contract and n_components remain correct.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import scipy.linalg as sla

# Threshold below which an eigenvalue is treated as zero.
_ZERO_TOL = 1e-8


def spectral_partition(edges: list[tuple], n: int) -> dict:
    """Spectrally partition an undirected weighted graph (BROKEN variant).

    See the gold reference / TASK.md for the intended contract. This variant
    reads the Fiedler value/vector from the WRONG eigenvalue index.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

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

    L = nx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray().astype(float)

    eigvals, eigvecs = sla.eigh(L)
    order = np.argsort(eigvals)
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    n_components = int(np.sum(eigvals < _ZERO_TOL))

    # DEFECT: index 0 (the smallest eigenvalue, always ~0) instead of index 1.
    fiedler_value = float(eigvals[0])
    fiedler_vec = eigvecs[:, 0]

    partition = [0 if val >= 0 else 1 for val in fiedler_vec]
    connected = bool(fiedler_value > _ZERO_TOL)

    return {
        "fiedler_value": fiedler_value,
        "partition": partition,
        "connected": connected,
        "n_components": n_components,
    }
