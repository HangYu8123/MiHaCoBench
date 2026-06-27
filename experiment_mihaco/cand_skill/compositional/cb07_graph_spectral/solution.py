import numpy as np
import scipy.linalg
import networkx as nx


def spectral_partition(edges: list[tuple], n: int) -> dict:
    """
    Perform spectral partition of an undirected weighted graph.

    Parameters
    ----------
    edges : list of (u, v, w) tuples
        Edges of the graph. u and v are node indices in [0, n),
        w is a positive edge weight.
    n : int
        Number of nodes (nodes are labeled 0..n-1).

    Returns
    -------
    dict with keys:
        fiedler_value : float
            Second-smallest eigenvalue of the Laplacian (algebraic connectivity).
        partition : list[int]
            Length-n list; entry i is 0 if Fiedler vector[i] >= 0, else 1.
        connected : bool
            True iff fiedler_value > 1e-8.
        n_components : int
            Number of connected components = count of eigenvalues < 1e-8.

    Raises
    ------
    ValueError
        If n < 1, any node index is out of [0, n), or any edge weight <= 0.
    """
    # --- Input validation ---
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    for edge in edges:
        u, v, w = edge
        if u < 0 or u >= n:
            raise ValueError(
                f"Node index u={u} is out of range [0, {n})"
            )
        if v < 0 or v >= n:
            raise ValueError(
                f"Node index v={v} is out of range [0, {n})"
            )
        if w <= 0:
            raise ValueError(
                f"Edge weight w={w} must be positive (w > 0)"
            )

    # --- Special case: n=1 (single node, no second eigenvalue) ---
    if n == 1:
        return {
            "fiedler_value": 0.0,
            "partition": [0],
            "connected": False,
            "n_components": 1,
        }

    # --- Graph construction ---
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    # --- Laplacian formation (dense, fixed node ordering) ---
    L = nx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray()

    # --- Eigendecomposition (symmetric solver; returns ascending-sorted output) ---
    eigenvalues, eigenvectors = scipy.linalg.eigh(L)

    # Safety sort (eigh guarantees ascending order for real symmetric, but be safe)
    sort_idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[sort_idx]
    eigenvectors = eigenvectors[:, sort_idx]

    # --- Derive outputs ---
    fiedler_value = float(eigenvalues[1])
    fiedler_vec = eigenvectors[:, 1]

    partition = [0 if x >= 0 else 1 for x in fiedler_vec]

    n_components = int(np.sum(eigenvalues < 1e-8))
    connected = bool(eigenvalues[1] > 1e-8)

    return {
        "fiedler_value": fiedler_value,
        "partition": partition,
        "connected": connected,
        "n_components": n_components,
    }
