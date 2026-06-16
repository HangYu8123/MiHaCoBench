"""
Graph Laplacian Spectral Partition — Compositional 07
"""

import numpy as np
import scipy.linalg
import networkx as nx


def spectral_partition(edges: list[tuple], n: int) -> dict:
    """
    Perform spectral partition of an undirected weighted graph.

    Parameters
    ----------
    edges : list of (u, v, w) tuples
    n     : number of nodes (0 .. n-1)

    Returns
    -------
    dict with keys: fiedler_value, partition, connected, n_components
    """
    # --- Validate inputs ---
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    for edge in edges:
        u, v, w = edge
        if u < 0 or u >= n:
            raise ValueError(f"Edge references node {u} outside [0, {n})")
        if v < 0 or v >= n:
            raise ValueError(f"Edge references node {v} outside [0, {n})")
        if w <= 0:
            raise ValueError(f"Edge weight must be positive, got {w}")

    # --- Build the graph ---
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for u, v, w in edges:
        # If there are multiple edges between same pair, networkx will keep last;
        # but the spec doesn't mention multi-edges so we just add them.
        G.add_edge(u, v, weight=w)

    # --- Compute combinatorial Laplacian as dense array ---
    L = nx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray()

    # --- Eigendecomposition with symmetric solver ---
    eigenvalues, eigenvectors = scipy.linalg.eigh(L)

    # eigh already returns eigenvalues in ascending order, but sort explicitly
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # --- Fiedler value and vector (second-smallest eigenvalue) ---
    # For n=1, there is only one eigenvalue; Fiedler value is 0 by convention.
    if n >= 2:
        fiedler_value = float(eigenvalues[1])
        fiedler_vector = eigenvectors[:, 1]
    else:
        # Single node: fiedler value is 0, vector is [1]
        fiedler_value = 0.0
        fiedler_vector = eigenvectors[:, 0]

    # --- Partition based on sign of Fiedler vector ---
    partition = [0 if fiedler_vector[i] >= 0 else 1 for i in range(n)]

    # --- Connected component info from eigenvalue spectrum ---
    threshold = 1e-8
    n_components = int(np.sum(eigenvalues < threshold))
    connected = bool(fiedler_value > threshold)

    return {
        "fiedler_value": fiedler_value,
        "partition": partition,
        "connected": connected,
        "n_components": n_components,
    }
