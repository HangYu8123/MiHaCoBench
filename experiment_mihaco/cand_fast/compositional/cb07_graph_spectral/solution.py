import numpy as np
import scipy.linalg
import networkx as nx


def spectral_partition(edges: list[tuple], n: int) -> dict:
    """Perform a spectral partition of an undirected weighted graph.

    Parameters
    ----------
    edges : list of (u, v, w) tuples
        Undirected edges with positive weights.
    n : int
        Number of nodes (0 through n-1).

    Returns
    -------
    dict with keys: fiedler_value, partition, connected, n_components
    """
    # Validate n
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    # Validate edges
    for edge in edges:
        u, v, w = edge
        if u < 0 or u >= n:
            raise ValueError(f"Edge node u={u} is out of range [0, {n})")
        if v < 0 or v >= n:
            raise ValueError(f"Edge node v={v} is out of range [0, {n})")
        if w <= 0:
            raise ValueError(f"Edge weight w={w} must be positive (> 0)")

    # Build the graph with all n nodes
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for edge in edges:
        u, v, w = edge
        G.add_edge(u, v, weight=w)

    # Compute dense Laplacian with fixed node ordering
    L = nx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray()

    # Eigendecomposition (eigh returns ascending-sorted eigenvalues for symmetric matrices)
    eigenvalues, eigenvectors = scipy.linalg.eigh(L)

    # Handle n=1 edge case: only one eigenvalue exists, no index-1 possible
    if len(eigenvalues) < 2:
        return {
            "fiedler_value": 0.0,
            "partition": [0],
            "connected": False,
            "n_components": 1,
        }

    # Extract Fiedler value (second-smallest eigenvalue, index 1)
    fiedler_value = float(eigenvalues[1])

    # Extract Fiedler vector and partition nodes
    fiedler_vec = eigenvectors[:, 1]
    partition = [0 if x >= 0 else 1 for x in fiedler_vec]

    # Connectivity and component count from eigenvalue spectrum
    n_components = int(np.sum(eigenvalues < 1e-8))
    connected = bool(eigenvalues[1] > 1e-8)

    return {
        "fiedler_value": fiedler_value,
        "partition": partition,
        "connected": connected,
        "n_components": n_components,
    }
