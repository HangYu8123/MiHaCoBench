"""Grader for competitive/cp09_dependent_selection. Public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Two INDEPENDENT ground-truth oracles, neither sharing the gold's Dinic code:
  * ``_brute`` — enumerate all 2^n subsets, keep the constraint-closed ones, take
    the max value. Definitionally correct; used for n <= 16.
  * ``_ek_oracle`` — the same max-weight-closure optimum computed via an
    Edmonds-Karp (BFS-augmenting) max flow. Used for medium n where brute is
    infeasible; a self-consistency test asserts it agrees with ``_brute`` on small
    instances first.

The broken reference is the natural "take all positives + close" greedy, which
returns a feasible but sub-optimal value whenever a positive item's forced
dependencies are net-negative. The discriminator + random + medium tests catch it;
trivial/no-constraint/all-negative tests pass on both.
"""
from __future__ import annotations

import random
from collections import deque

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "competitive", "cp09_dependent_selection"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
best_selection_value = gu.load_callable(SOL, "solution.py", "best_selection_value")


# ---------------------------------------------------------------------------
# Oracle 1: brute force over all subsets (n <= ~16).
# ---------------------------------------------------------------------------

def _brute(values: list[int], requires: list[tuple[int, int]]) -> int:
    n = len(values)
    best = 0
    for mask in range(1 << n):
        in_s = [(mask >> i) & 1 for i in range(n)]
        if all((not in_s[a]) or in_s[b] for a, b in requires):
            total = sum(values[i] for i in range(n) if in_s[i])
            if total > best:
                best = total
    return best


# ---------------------------------------------------------------------------
# Oracle 2: independent Edmonds-Karp max flow on the closure reduction.
# ---------------------------------------------------------------------------

def _ek_oracle(values: list[int], requires: list[tuple[int, int]]) -> int:
    n = len(values)
    if n == 0:
        return 0
    inf = sum(abs(v) for v in values) + 1
    s, t = n, n + 1
    size = n + 2
    cap: list[dict] = [dict() for _ in range(size)]

    def add(u, v, c):
        cap[u][v] = cap[u].get(v, 0) + c
        cap[v].setdefault(u, 0)

    pos_total = 0
    for i, v in enumerate(values):
        if v > 0:
            add(s, i, v)
            pos_total += v
        elif v < 0:
            add(i, t, -v)
    for a, b in requires:
        if a != b:
            add(a, b, inf)

    flow = 0
    while True:
        parent = [-1] * size
        parent[s] = s
        q = deque([s])
        while q:
            u = q.popleft()
            for v, c in cap[u].items():
                if c > 0 and parent[v] == -1:
                    parent[v] = u
                    q.append(v)
        if parent[t] == -1:
            break
        bottleneck = inf
        v = t
        while v != s:
            u = parent[v]
            bottleneck = min(bottleneck, cap[u][v])
            v = u
        v = t
        while v != s:
            u = parent[v]
            cap[u][v] -= bottleneck
            cap[v][u] = cap[v].get(u, 0) + bottleneck
            v = u
        flow += bottleneck
    return pos_total - flow


def _rand_instance(rng, n, n_constraints, lo=-20, hi=20):
    values = [rng.randint(lo, hi) for _ in range(n)]
    requires = []
    for _ in range(n_constraints):
        a = rng.randrange(n)
        b = rng.randrange(n)
        if a != b:
            requires.append((a, b))
    return values, requires


# ---------------------------------------------------------------------------
# 1. Trivial / boundary cases.
# ---------------------------------------------------------------------------

def test_trivial():
    assert best_selection_value([], []) == 0
    assert best_selection_value([7], []) == 7
    assert best_selection_value([-7], []) == 0
    assert best_selection_value([0], []) == 0


# ---------------------------------------------------------------------------
# 2. No constraints -> sum of positives.
# ---------------------------------------------------------------------------

def test_no_constraints():
    vals = [5, -3, 8, -1, 2]
    assert best_selection_value(vals, []) == 5 + 8 + 2


# ---------------------------------------------------------------------------
# 3. Worked examples from TASK.md.
# ---------------------------------------------------------------------------

def test_worked_examples():
    assert best_selection_value([10, -100], [(0, 1)]) == 0
    assert best_selection_value([10, 5, -3], [(0, 2)]) == 12


# ---------------------------------------------------------------------------
# 4. The discriminator: a positive item forcing a net-negative dependency.
#    Optimum drops it; the greedy keeps it.
# ---------------------------------------------------------------------------

def test_positive_requires_negative_drop():
    # Selecting item 0 (+10) forces item 1 (-100): better to select nothing.
    assert best_selection_value([10, -100], [(0, 1)]) == 0
    # Two independent profitable groups, one poisoned by a heavy dependency.
    values = [10, -100, 20, -5]
    requires = [(0, 1), (2, 3)]  # group {0,1}=-90 (drop), group {2,3}=15 (keep)
    assert best_selection_value(values, requires) == 15


# ---------------------------------------------------------------------------
# 5. Cyclic constraints — all-or-nothing groups.
# ---------------------------------------------------------------------------

def test_cycle_constraints():
    # 0<->1 cycle, together = +3; vs nothing = 0.
    assert best_selection_value([5, -2], [(0, 1), (1, 0)]) == 3
    # 0<->1 cycle, together = -3 -> drop.
    assert best_selection_value([5, -8], [(0, 1), (1, 0)]) == 0


# ---------------------------------------------------------------------------
# 6. Many random small instances vs the brute oracle.
# ---------------------------------------------------------------------------

def test_random_small_vs_brute():
    rng = random.Random(2026)
    for _ in range(400):
        n = rng.randint(1, 12)
        values, requires = _rand_instance(rng, n, rng.randint(0, n * 2))
        assert best_selection_value(values, requires) == _brute(values, requires), \
            f"values={values} requires={requires}"


# ---------------------------------------------------------------------------
# 7. Oracle self-consistency: the EK oracle agrees with brute on small instances.
# ---------------------------------------------------------------------------

def test_oracle_self_consistency():
    rng = random.Random(7)
    for _ in range(200):
        n = rng.randint(1, 12)
        values, requires = _rand_instance(rng, n, rng.randint(0, n * 2))
        assert _ek_oracle(values, requires) == _brute(values, requires)


# ---------------------------------------------------------------------------
# 8. Medium instances vs the EK oracle — n far beyond any feasible subset search.
#    A brute-force candidate cannot run these; a wrong heuristic gives wrong values.
# ---------------------------------------------------------------------------

def test_medium_vs_ek():
    rng = random.Random(99)
    for _ in range(40):
        n = rng.randint(50, 75)
        values, requires = _rand_instance(rng, n, rng.randint(n, 3 * n), lo=-15, hi=15)
        assert best_selection_value(values, requires) == _ek_oracle(values, requires), \
            f"mismatch at n={n}"


# ---------------------------------------------------------------------------
# 9. Structured larger instance with a known optimum (chains of profitable pairs).
# ---------------------------------------------------------------------------

def test_structured_large():
    # k pairs: item 2i (+3) requires item 2i+1 (-1) -> each pair nets +2.
    k = 150
    values = []
    requires = []
    for i in range(k):
        values.append(3)   # 2i
        values.append(-1)  # 2i+1
        requires.append((2 * i, 2 * i + 1))
    # plus some standalone poison-positives requiring a huge negative (must be dropped)
    base = len(values)
    values.append(50)        # base
    values.append(-1000)     # base+1
    requires.append((base, base + 1))
    assert best_selection_value(values, requires) == 2 * k  # all good pairs, poison dropped


# ---------------------------------------------------------------------------
# 10. Advisory code-quality report (never asserted).
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    print("code_quality:", gu.code_quality_report(SOL))
