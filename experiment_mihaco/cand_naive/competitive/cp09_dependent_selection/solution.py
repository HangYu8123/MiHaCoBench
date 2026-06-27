"""
cp09_dependent_selection — maximum-value selection under "requires" constraints.

Approach: Project-selection / closure problem, reduced to max-flow (min-cut).

1. Condense strongly-connected components (Kosaraju) so cycles become single
   super-nodes with summed values.
2. Build a flow network:
   - Source S connects to every super-node with positive total value  (cap = value).
   - Every super-node with negative total value connects to Sink T    (cap = |value|).
   - For each condensed dependency edge u->v (u requires v) add an arc with
     capacity infinity.
3. Answer = sum_of_positive_values  –  max_flow(S, T).
   (Selecting nothing is always an option, so answer >= 0.)
"""

from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# Dinic's max-flow (standard library only)
# ---------------------------------------------------------------------------

class _Dinic:
    """Dinic's algorithm for max-flow.  O(V^2 * E) in general."""

    def __init__(self, n: int):
        self.n = n
        self.graph: list[list[list]] = [[] for _ in range(n)]
        # Each edge stored as [to, cap, rev_index]

    def add_edge(self, u: int, v: int, cap: int):
        fwd = [v, cap, len(self.graph[v])]
        bwd = [u, 0,  len(self.graph[u])]
        self.graph[u].append(fwd)
        self.graph[v].append(bwd)

    def _bfs(self, s: int, t: int) -> bool:
        self.level = [-1] * self.n
        self.level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v, cap, _ in self.graph[u]:
                if cap > 0 and self.level[v] < 0:
                    self.level[v] = self.level[u] + 1
                    q.append(v)
        return self.level[t] >= 0

    def _dfs(self, u: int, t: int, f: int, it: list) -> int:
        if u == t:
            return f
        while it[u] < len(self.graph[u]):
            e = self.graph[u][it[u]]
            v, cap, ri = e
            if cap > 0 and self.level[v] == self.level[u] + 1:
                d = self._dfs(v, t, min(f, cap), it)
                if d > 0:
                    e[1] -= d
                    self.graph[v][ri][1] += d
                    return d
            it[u] += 1
        return 0

    def max_flow(self, s: int, t: int) -> int:
        flow = 0
        INF = float('inf')
        while self._bfs(s, t):
            it = [0] * self.n
            while True:
                f = self._dfs(s, t, INF, it)
                if f == 0:
                    break
                flow += f
        return flow


# ---------------------------------------------------------------------------
# Kosaraju's SCC
# ---------------------------------------------------------------------------

def _kosaraju(n: int, adj: list[list[int]], radj: list[list[int]]) -> list[int]:
    """Returns comp[i] = SCC id of node i (0-indexed)."""
    visited = [False] * n
    order: list[int] = []

    def dfs1(u: int):
        stack = [(u, 0)]
        while stack:
            v, idx = stack[-1]
            if not visited[v]:
                visited[v] = True
            found = False
            while idx < len(adj[v]):
                w = adj[v][idx]
                idx += 1
                stack[-1] = (v, idx)
                if not visited[w]:
                    stack.append((w, 0))
                    found = True
                    break
            if not found:
                if stack[-1][0] == v:
                    stack.pop()
                    order.append(v)

    for i in range(n):
        if not visited[i]:
            dfs1(i)

    comp = [-1] * n
    c = 0

    def dfs2(u: int, c: int):
        stack = [u]
        comp[u] = c
        while stack:
            v = stack.pop()
            for w in radj[v]:
                if comp[w] < 0:
                    comp[w] = c
                    stack.append(w)

    for u in reversed(order):
        if comp[u] < 0:
            dfs2(u, c)
            c += 1

    return comp


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def best_selection_value(values: list[int], requires: list[tuple[int, int]]) -> int:
    n = len(values)
    if n == 0:
        return 0

    # Build adjacency lists
    adj:  list[list[int]] = [[] for _ in range(n)]
    radj: list[list[int]] = [[] for _ in range(n)]
    for a, b in requires:
        if a == b:
            continue
        adj[a].append(b)
        radj[b].append(a)

    # Kosaraju SCC
    comp = _kosaraju(n, adj, radj)
    num_scc = max(comp) + 1 if n > 0 else 0

    # Aggregate values per SCC
    scc_val = [0] * num_scc
    for i in range(n):
        scc_val[comp[i]] += values[i]

    # Build condensed graph (DAG edges between SCCs)
    cond_edges: set[tuple[int, int]] = set()
    for a, b in requires:
        ca, cb = comp[a], comp[b]
        if ca != cb:
            cond_edges.add((ca, cb))

    # Project-selection flow network
    # Nodes: 0..num_scc-1 are SCC nodes, num_scc = source, num_scc+1 = sink
    S = num_scc
    T = num_scc + 1
    total_nodes = num_scc + 2

    dinic = _Dinic(total_nodes)
    INF = 10 ** 18

    positive_sum = 0
    for c_id in range(num_scc):
        v = scc_val[c_id]
        if v > 0:
            positive_sum += v
            dinic.add_edge(S, c_id, v)
        elif v < 0:
            dinic.add_edge(c_id, T, -v)

    for ca, cb in cond_edges:
        dinic.add_edge(ca, cb, INF)

    mf = dinic.max_flow(S, T)
    return max(0, positive_sum - mf)
