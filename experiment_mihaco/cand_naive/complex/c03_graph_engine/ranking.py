"""Graph ranking algorithms: PageRank, degree centrality."""

import numpy as np


def pagerank(graph, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-9) -> dict:
    """Compute the PageRank of every node using power iteration.

    The returned dict:
    - contains every node in the graph
    - has values summing to approximately 1.0 (within 1e-6)
    - converges within max_iter power-iterations

    Formula: PR(v) = (1-d)/N + d * sum(PR(u)/out_degree(u)) for each in-neighbour u
    """
    nodes = list(graph.nodes())
    N = len(nodes)

    if N == 0:
        return {}

    if N == 1:
        return {nodes[0]: 1.0}

    # Create node -> index mapping
    node_idx = {node: i for i, node in enumerate(nodes)}

    # Build transition matrix (column-stochastic)
    # For each node, compute out-degree and build adjacency info
    out_degree = np.zeros(N)
    # adjacency: target_idx -> list of (source_idx, weight) pairs
    # We need for each node v: sum over u that points to v of PR(u)/out_degree(u)
    # Build a sparse representation: for node u, it contributes to neighbors

    # Build the transition matrix M where M[v][u] = 1/out_degree(u) if u->v edge
    # PR_new = (1-d)/N * ones + d * M @ PR

    # Use numpy arrays for efficiency
    M = np.zeros((N, N))

    for node in nodes:
        u_idx = node_idx[node]
        neighbors_list = list(graph.neighbors(node))

        if len(neighbors_list) == 0:
            # Dangling node: distribute evenly to all nodes
            M[:, u_idx] = 1.0 / N
        else:
            # Compute out-degree (sum of all outgoing edge weights, but standard PR uses count)
            # Standard PageRank uses uniform distribution over out-neighbors
            out_deg = len(neighbors_list)
            for neighbor, _ in neighbors_list:
                v_idx = node_idx[neighbor]
                M[v_idx, u_idx] += 1.0 / out_deg

    # Power iteration
    pr = np.ones(N) / N

    for _ in range(max_iter):
        pr_new = (1.0 - damping) / N * np.ones(N) + damping * M @ pr

        # Check convergence
        diff = np.abs(pr_new - pr).sum()
        pr = pr_new

        if diff < tol:
            break

    # Normalize to ensure sum = 1.0
    total = pr.sum()
    if total > 0:
        pr = pr / total

    return {node: float(pr[node_idx[node]]) for node in nodes}


def degree_centrality(graph) -> dict:
    """Return {node: degree / (N-1)} where N is the total number of nodes.

    For directed graphs, use the total degree (in + out).
    For N <= 1, return {node: 0.0} for all nodes.
    Every node in the graph must appear in the result.
    """
    nodes = list(graph.nodes())
    N = len(nodes)

    if N <= 1:
        return {node: 0.0 for node in nodes}

    result = {}

    if not graph.directed:
        # For undirected: degree = number of neighbors
        for node in nodes:
            deg = len(list(graph.neighbors(node)))
            result[node] = deg / (N - 1)
    else:
        # For directed: use total degree (in + out)
        out_degree = {node: 0 for node in nodes}
        in_degree = {node: 0 for node in nodes}

        for node in nodes:
            for neighbor, _ in graph.neighbors(node):
                out_degree[node] += 1
                in_degree[neighbor] += 1

        for node in nodes:
            total_deg = out_degree[node] + in_degree[node]
            result[node] = total_deg / (N - 1)

    return result
