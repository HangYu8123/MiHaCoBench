import heapq
from collections import defaultdict


def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    if n == 0:
        return []

    # Deduplicate edges to avoid inflated in-degrees
    unique_deps = set(deps)

    # Initialize in-degree and adjacency list for all nodes 0..n-1
    in_degree = [0] * n
    adj = defaultdict(list)

    for a, b in unique_deps:
        adj[a].append(b)
        in_degree[b] += 1

    # Initialize min-heap with all nodes that have in-degree 0
    heap = [i for i in range(n) if in_degree[i] == 0]
    heapq.heapify(heap)

    result = []

    while heap:
        node = heapq.heappop(heap)
        result.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    if len(result) != n:
        raise ValueError("cycle detected")

    return result
