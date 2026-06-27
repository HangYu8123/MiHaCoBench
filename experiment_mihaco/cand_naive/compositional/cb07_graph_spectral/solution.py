import numpy as np
import networkx as nx
import scipy.linalg


def spectral_partition(edges: list[tuple], n: int) -> dict:
    """
    Perform spectral partition of an undirected weighted graph.

    Parameters
    ----------
    edges : list of (u, v, w) tuples
        Undirected edges with positive weights.
    n : int
        Number of nodes (0 to n-1).

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
            raise ValueError(f"Node index {u} is out of range [0, {n})")
        if v < 0 or v >= n:
            raise ValueError(f"Node index {v} is out of range [0, {n})")
        if w <= 0:
            raise ValueError(f"Edge weight {w} must be positive")

    # Build networkx graph with all n nodes
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    # Form the combinatorial Laplacian as a dense numpy array
    L = nx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray()

    # Compute eigenvalues and eigenvectors using symmetric solver
    eigenvalues, eigenvectors = scipy.linalg.eigh(L)

    # Sort ascending by eigenvalue (eigh already returns sorted, but be explicit)
    sort_idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[sort_idx]
    eigenvectors = eigenvectors[:, sort_idx]

    # Fiedler value: second-smallest eigenvalue (index 1)
    fiedler_value = float(eigenvalues[1])

    # Fiedler vector: eigenvector corresponding to second-smallest eigenvalue
    fiedler_vector = eigenvectors[:, 1]

    # Partition: 0 if fiedler_vector[i] >= 0, else 1
    partition = [0 if x >= 0 else 1 for x in fiedler_vector]

    # Connected: second-smallest eigenvalue > 1e-8
    connected = bool(fiedler_value > 1e-8)

    # Number of components: number of eigenvalues < 1e-8
    n_components = int(np.sum(eigenvalues < 1e-8))

    return {
        "fiedler_value": fiedler_value,
        "partition": partition,
        "connected": connected,
        "n_components": n_components,
    }
