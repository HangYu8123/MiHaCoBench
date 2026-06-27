"""Broken reference for competitive/cp09_dependent_selection.

PLANTED DEFECT (the natural-but-wrong approach): greedily select every item with a
positive value, then pull in the transitive closure of everything they require,
and sum that set. This is the intuitive first instinct, but it is wrong: forcing
in a positive item can drag in required items whose combined cost makes the whole
group net-negative — in which case the optimum is to drop that positive item
entirely. The greedy keeps it, yielding a feasible but sub-optimal (sometimes even
negative) total. Only a min-cut / max-weight-closure argument finds the true
optimum.
"""
from __future__ import annotations

from collections import deque


def best_selection_value(values: list[int], requires: list[tuple[int, int]]) -> int:
    """BROKEN: greedily take all positive items + their required closure."""
    n = len(values)
    if n == 0:
        return 0
    adj: list[list[int]] = [[] for _ in range(n)]
    for a, b in requires:
        adj[a].append(b)

    selected = [values[i] > 0 for i in range(n)]
    dq = deque(i for i in range(n) if selected[i])
    while dq:
        u = dq.popleft()
        for b in adj[u]:
            if not selected[b]:
                selected[b] = True
                dq.append(b)

    return sum(values[i] for i in range(n) if selected[i])
