"""
Compositional 07 — graph_spectral: Graph Laplacian Spectral Partition

Performs spectral partition of an undirected weighted graph by composing:
- networkx (graph construction + Laplacian)
- scipy.linalg (symmetric eigendecomposition)
- numpy (array work)
"""

import numpy as np
import networkx as nx
from scipy.linalg import eigh


def spectral_partition(edges: list[tuple], n: int) -> dict:
    """
    Perform spectral partition of an undirected weighted graph.

    Parameters
    ----------
    edges : list[tuple]
        List of (u, v, w) tuples describing undirected weighted edges.
        u and v are node indices in [0, n), w is a positive edge weight.
    n : int
        Number of nodes; nodes are integers 0, 1, ..., n-1.

    Returns
    -------
    dict with keys:
        fiedler_value : float
            The second-smallest eigenvalue (algebraic connectivity).
        partition : list[int]
            Length n. Entry i is 0 if Fiedler-vector entry >= 0, else 1.
        connected : bool
            True iff the graph is connected (second-smallest eigenvalue > 1e-8).
        n_components : int
            Number of connected components = number of eigenvalues < 1e-8.

    Raises
    ------
    ValueError
        If n < 1, or any edge references a node outside [0, n),
        or any edge has a non-positive weight.
    """
    # Validate n
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    # Validate all edges before building the graph
    for edge in edges:
        u, v, w = edge
        if u < 0 or u >= n or v < 0 or v >= n:
            raise ValueError(
                f"Edge ({u}, {v}, {w}) references node outside [0, {n})"
            )
        if w <= 0:
            raise ValueError(
                f"Edge ({u}, {v}, {w}) has non-positive weight {w}"
            )

    # Build the graph
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for edge in edges:
        u, v, w = edge
        G.add_edge(u, v, weight=w)

    # Form the combinatorial Laplacian as a dense numpy array
    L = nx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray()

    # Handle n=1 edge case: only one eigenvalue (0), no Fiedler value
    if n == 1:
        return {
            "fiedler_value": 0.0,
            "partition": [0],
            "connected": False,
            "n_components": 1,
        }

    # Compute eigenvalues and eigenvectors using symmetric solver
    # eigh returns eigenvalues in ascending order by default
    eigenvalues, eigenvectors = eigh(L)

    # Extract Fiedler value (second-smallest eigenvalue, index 1)
    fiedler_value = float(eigenvalues[1])

    # Extract Fiedler vector (column at index 1)
    fiedler_vector = eigenvectors[:, 1]

    # Build partition: 0 if Fiedler vector entry >= 0, else 1
    partition = [0 if fiedler_vector[i] >= 0 else 1 for i in range(n)]

    # Determine connectivity from eigenvalue spectrum
    connected = bool(eigenvalues[1] > 1e-8)

    # Count connected components: number of eigenvalues < 1e-8
    n_components = int(np.sum(eigenvalues < 1e-8))

    return {
        "fiedler_value": fiedler_value,
        "partition": partition,
        "connected": connected,
        "n_components": n_components,
    }
