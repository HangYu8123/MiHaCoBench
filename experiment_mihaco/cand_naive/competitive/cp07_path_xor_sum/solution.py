from collections import deque

MOD = 1_000_000_007


def sum_path_xor(n: int, edges: list[tuple[int, int, int]]) -> int:
    if n == 1:
        return 0

    # Build adjacency list
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    # BFS from node 0 to compute XOR distance from root to each node
    # dist[v] = XOR of edge weights on path from root (0) to v
    dist = [0] * n
    visited = [False] * n
    queue = deque([0])
    visited[0] = True

    while queue:
        u = queue.popleft()
        for v, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                dist[v] = dist[u] ^ w
                queue.append(v)

    # For each bit k, count nodes with that bit set in dist
    # pathxor(a, b) = dist[a] ^ dist[b]
    # Bit k is set in pathxor(a,b) iff exactly one of dist[a], dist[b] has bit k set
    # Contribution of bit k = (count with bit set) * (count without bit set) * (1 << k)
    result = 0
    for k in range(30):
        bit = 1 << k
        count_set = sum(1 for d in dist if d & bit)
        count_unset = n - count_set
        result = (result + count_set * count_unset % MOD * bit) % MOD

    return result
