import heapq


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    """
    Returns the lexicographically-smallest topological ordering of n tasks
    (labelled 0 through n-1) given dependency edges.

    Each edge (a, b) means task a must complete before task b.
    Duplicate edges are deduplicated. Self-loops indicate cycles.

    Raises ValueError if the graph contains a cycle.

    Time complexity: O((V + E) log V) — in practice well within the 5s gate
    for V=200000, E=400000 in CPython 3.11.
    """
    # --- Build graph with deduplication ---
    # Dedup edges: convert to a set so duplicate (a,b) pairs are collapsed.
    # This is critical: without dedup, duplicate edges inflate in_degree[b]
    # beyond the number of decrements we perform, permanently blocking b.
    edge_set = set(deps)

    adj: list[list[int]] = [[] for _ in range(n)]
    in_degree: list[int] = [0] * n

    for a, b in edge_set:
        adj[a].append(b)
        in_degree[b] += 1

    # --- Kahn's algorithm with min-heap for lex-smallest order ---
    # Initialize heap with all nodes whose in-degree is 0.
    heap: list[int] = [v for v in range(n) if in_degree[v] == 0]
    heapq.heapify(heap)

    result: list[int] = []

    while heap:
        v = heapq.heappop(heap)  # always pick the smallest-index ready node
        result.append(v)
        for u in adj[v]:
            in_degree[u] -= 1
            if in_degree[u] == 0:
                heapq.heappush(heap, u)

    # --- Cycle detection ---
    # If some nodes were never enqueued (in_degree never reached 0),
    # there is a cycle (including self-loops).
    if len(result) < n:
        raise ValueError("cycle detected")

    return result
