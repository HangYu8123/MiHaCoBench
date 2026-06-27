"""Gold reference for competitive/cp09_dependent_selection.

Choose a subset S of items maximising the sum of their (possibly negative) values,
subject to: for every constraint (a, b), if a in S then b in S. This is the
**maximum-weight closure** problem, and the key (non-obvious) observation is that
it reduces to a minimum s-t cut:

    source s --(value_i)--> i            for every item with value_i > 0
    i --(-value_i)--> sink t             for every item with value_i < 0
    a --(infinity)--> b                  for every constraint (a requires b)

    answer = (sum of all positive values) - maxflow(s, t)

A node left on the source side of the min cut is "selected"; the infinite
constraint edges force the closure property (you can never cut an infinite edge,
so selecting `a` forces selecting `b`). The greedy "take every positive item and
pull in its dependencies" is wrong, because a positive item can drag in
dependencies whose combined cost makes the group net-negative.

Max flow is computed with Dinic's algorithm; capacities are integers
(``INF = sum|value| + 1`` is larger than any real cut).
"""
from __future__ import annotations

from collections import deque


class _Dinic:
    def __init__(self, n: int) -> None:
        self.n = n
        self.graph: list[list[list]] = [[] for _ in range(n)]  # [to, cap, rev_index]

    def add_edge(self, u: int, v: int, cap: int) -> None:
        self.graph[u].append([v, cap, len(self.graph[v])])
        self.graph[v].append([u, 0, len(self.graph[u]) - 1])

    def _bfs(self, s: int, t: int, level: list[int]) -> bool:
        for i in range(self.n):
            level[i] = -1
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for to, cap, _ in self.graph[u]:
                if cap > 0 and level[to] < 0:
                    level[to] = level[u] + 1
                    q.append(to)
        return level[t] >= 0

    def _dfs(self, u: int, t: int, pushed: int, level: list[int], it: list[int]) -> int:
        if u == t:
            return pushed
        while it[u] < len(self.graph[u]):
            edge = self.graph[u][it[u]]
            to, cap, rev = edge
            if cap > 0 and level[to] == level[u] + 1:
                d = self._dfs(to, t, min(pushed, cap), level, it)
                if d > 0:
                    edge[1] -= d
                    self.graph[to][rev][1] += d
                    return d
            it[u] += 1
        return 0

    def max_flow(self, s: int, t: int) -> int:
        flow = 0
        level = [-1] * self.n
        while self._bfs(s, t, level):
            it = [0] * self.n
            while True:
                f = self._dfs(s, t, float("inf"), level, it)  # type: ignore[arg-type]
                if f == 0:
                    break
                flow += f
        return flow


def best_selection_value(values: list[int], requires: list[tuple[int, int]]) -> int:
    """Maximum total value of a constraint-closed subset of items.

    Parameters
    ----------
    values : list[int]
        ``values[i]`` is the (possibly negative) value of item ``i`` (items 0..n-1).
    requires : list[tuple[int, int]]
        Each ``(a, b)`` means "selecting item ``a`` requires also selecting item ``b``".

    Returns
    -------
    int
        The maximum achievable sum of values over all subsets ``S`` such that for
        every ``(a, b)`` in ``requires``, ``a in S`` implies ``b in S``. The empty
        subset is always allowed, so the answer is never negative.
    """
    n = len(values)
    if n == 0:
        return 0
    inf = sum(abs(v) for v in values) + 1
    s, t = n, n + 1
    dinic = _Dinic(n + 2)
    positive_total = 0
    for i, v in enumerate(values):
        if v > 0:
            dinic.add_edge(s, i, v)
            positive_total += v
        elif v < 0:
            dinic.add_edge(i, t, -v)
    for a, b in requires:
        if a != b:
            dinic.add_edge(a, b, inf)
    return positive_total - dinic.max_flow(s, t)
