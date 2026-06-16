"""Grader for competitive/cp06_range_distinct_offline. Tests the public contract
only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Public contract under test:
    range_distinct(a: list[int], queries: list[tuple]) -> list[int]
returns, per (l, r) 0-indexed inclusive query, the count of DISTINCT values in
``a[l..r]``, in the SAME order as the input queries.

Independent reference (used only on SMALL inputs, never on the gate):
    [len(set(a[l:r + 1])) for (l, r) in queries]

Test catalogue (>=10 required for competitive):
   1. test_single_element              — n=1, the only valid query
   2. test_whole_array_query           — one (0, n-1) query over the full array
   3. test_many_singleton_ranges       — every (i, i) query -> all 1s
   4. test_all_distinct_array          — values all different
   5. test_all_equal_array             — values all identical
   6. test_order_preservation          — answers follow INPUT query order, not r-order
   7. test_empty_queries               — [] -> []
   8. test_random_small_vs_reference   — many random small cases vs the set() oracle
   9. test_adversarial_random_pattern  — structured adversarial small case vs oracle
  10. test_hard_time_gate              — N=Q=150000 fixed seed, timeout 8s (HARD gate)
  11. test_soft_complexity             — empirical curve fit (advisory, >2 tiers -> fail)
  12. test_code_quality                — advisory only (never asserted)
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "competitive", "cp06_range_distinct_offline"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
range_distinct = gu.load_callable(SOL, "solution.py", "range_distinct")

# Hard-gate parameters — MUST match TASK.md exactly.
GATE_N = 150_000
GATE_Q = 150_000
GATE_SEED = 42
GATE_ALPHABET = 300
GATE_TIMEOUT = 8.0


# ---------------------------------------------------------------------------
# Independent reference (correct but O(n) per query). SMALL inputs only.
# ---------------------------------------------------------------------------

def _reference(a: list[int], queries: list[tuple]) -> list[int]:
    """Brute-force oracle: count distinct values in each inclusive slice."""
    return [len(set(a[l:r + 1])) for (l, r) in queries]


def _build_gate_input(n: int, q: int, seed: int, alphabet: int):
    """Deterministically build the large adversarial (a, queries) gate input.

    Values are drawn from a modest alphabet so distinctness varies; queries are
    random valid (l, r) inclusive ranges. Fixed seed -> reproducible.
    """
    rng = random.Random(seed)
    a = [rng.randint(0, alphabet - 1) for _ in range(n)]
    queries = []
    for _ in range(q):
        l = rng.randint(0, n - 1)
        r = rng.randint(l, n - 1)
        queries.append((l, r))
    return a, queries


# ---------------------------------------------------------------------------
# 1. Single element
# ---------------------------------------------------------------------------

def test_single_element():
    assert range_distinct([7], [(0, 0)]) == [1]


# ---------------------------------------------------------------------------
# 2. Whole-array query
# ---------------------------------------------------------------------------

def test_whole_array_query():
    a = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
    queries = [(0, len(a) - 1)]
    expected = _reference(a, queries)
    assert range_distinct(a, queries) == expected
    assert range_distinct(a, queries) == [7]  # {3,1,4,5,9,2,6}


# ---------------------------------------------------------------------------
# 3. Many singleton-range queries -> every answer is 1
# ---------------------------------------------------------------------------

def test_many_singleton_ranges():
    a = [5, 5, 9, 1, 1, 1, 2, 8, 8, 4]
    queries = [(i, i) for i in range(len(a))]
    expected = _reference(a, queries)
    result = range_distinct(a, queries)
    assert result == expected
    assert result == [1] * len(a)


# ---------------------------------------------------------------------------
# 4. All-distinct array
# ---------------------------------------------------------------------------

def test_all_distinct_array():
    a = list(range(12))  # every value unique
    queries = [(0, 0), (0, 11), (3, 7), (5, 11), (11, 11), (2, 9)]
    expected = _reference(a, queries)
    result = range_distinct(a, queries)
    assert result == expected
    # for a strictly-distinct array, the answer is just the range length
    assert result == [r - l + 1 for (l, r) in queries]


# ---------------------------------------------------------------------------
# 5. All-equal array
# ---------------------------------------------------------------------------

def test_all_equal_array():
    a = [4] * 10
    queries = [(0, 0), (0, 9), (2, 8), (4, 4), (1, 6)]
    expected = _reference(a, queries)
    result = range_distinct(a, queries)
    assert result == expected
    assert result == [1, 1, 1, 1, 1]  # always exactly one distinct value


# ---------------------------------------------------------------------------
# 6. Order preservation — result order follows INPUT query order, not r-order
# ---------------------------------------------------------------------------

def test_order_preservation():
    a = [1, 2, 2, 3, 1, 4, 2, 5]
    # Intentionally NOT sorted by r: a correct offline solver must restore the
    # original input ordering of the answers.
    queries = [(0, 7), (0, 0), (2, 5), (6, 7), (1, 3), (0, 4)]
    expected = _reference(a, queries)
    result = range_distinct(a, queries)
    assert result == expected
    # Shuffling the queries must permute the answers identically.
    perm = [4, 0, 5, 2, 1, 3]
    shuffled = [queries[i] for i in perm]
    shuffled_result = range_distinct(a, shuffled)
    assert shuffled_result == [result[i] for i in perm]


# ---------------------------------------------------------------------------
# 7. Empty query list
# ---------------------------------------------------------------------------

def test_empty_queries():
    assert range_distinct([1, 2, 3], []) == []
    assert range_distinct([], []) == []


# ---------------------------------------------------------------------------
# 8. Many random small cases vs the set() reference
# ---------------------------------------------------------------------------

def test_random_small_vs_reference():
    rng = random.Random(20240616)
    for _ in range(300):
        n = rng.randint(1, 40)
        alphabet = rng.randint(1, 8)  # small alphabet -> distinctness varies
        a = [rng.randint(0, alphabet - 1) for _ in range(n)]
        queries = []
        for _ in range(rng.randint(0, 15)):
            l = rng.randint(0, n - 1)
            r = rng.randint(l, n - 1)
            queries.append((l, r))
        expected = _reference(a, queries)
        assert range_distinct(a, queries) == expected, (a, queries)


# ---------------------------------------------------------------------------
# 9. Structured adversarial small case vs oracle
# ---------------------------------------------------------------------------

def test_adversarial_random_pattern():
    """A pattern with many repeated values whose latest occurrence migrates as r
    grows — this defeats any solver that mishandles the last-occurrence update."""
    # value v appears at many positions; distinct count must track unique values.
    a = [0, 1, 0, 2, 1, 0, 3, 2, 1, 0, 4, 3, 2, 1, 0]
    queries = []
    for l in range(len(a)):
        for r in range(l, len(a)):
            queries.append((l, r))
    # query order deliberately not sorted by r
    rng = random.Random(99)
    rng.shuffle(queries)
    expected = _reference(a, queries)
    assert range_distinct(a, queries) == expected


# ---------------------------------------------------------------------------
# 10. HARD time gate: N=Q=150000, fixed seed, timeout 8s
# ---------------------------------------------------------------------------

def test_hard_time_gate():
    """N=Q=150000 random instance (fixed seed) must finish within 8 seconds.

    The O((n + q) log n) Fenwick offline solver finishes in well under a second
    here. The naive O(n * q) per-query ``len(set(a[l:r+1]))`` approach needs on
    the order of 1e10 operations (~100s) and TIMES OUT.
    """
    a, queries = _build_gate_input(GATE_N, GATE_Q, GATE_SEED, GATE_ALPHABET)
    result = gu.run_within(GATE_TIMEOUT, range_distinct, a, queries)
    # Basic shape sanity.
    assert isinstance(result, list)
    assert len(result) == GATE_Q
    assert all(isinstance(x, int) for x in result)
    # Distinct count is bounded by both range length and alphabet size.
    for (l, r), c in zip(queries[:2000], result[:2000]):
        assert 1 <= c <= min(r - l + 1, GATE_ALPHABET)
    # Spot-check a small slice of the SAME instance against the brute oracle.
    spot = list(range(0, GATE_Q, GATE_Q // 200))
    for qi in spot:
        l, r = queries[qi]
        assert result[qi] == len(set(a[l:r + 1]))


# ---------------------------------------------------------------------------
# 11. SOFT complexity signal (advisory)
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    """Empirical fit — advisory; fails only if the estimate is >2 tiers above the
    O(n log n) target. The hard gate is the real discriminator.

    Sizes are kept small so even an O(n*q) submission completes here; we scale
    n and q together so the input size parameter is n.
    """
    sizes = [400, 800, 1200, 1600, 2000]

    def make_input(n: int):
        rng = random.Random(n)
        a = [rng.randint(0, 50) for _ in range(n)]
        queries = []
        for _ in range(n):  # q == n
            l = rng.randint(0, n - 1)
            r = rng.randint(l, n - 1)
            queries.append((l, r))
        return a, queries

    timings = gu.measure_runtime(
        make_input,
        lambda args: range_distinct(args[0], args[1]),
        sizes,
        repeats=2,
    )
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n log n)  "
          f"ranked={report['ranked'][:3]}")
    # Allow up to O(n^2) — within one tier of the worst tolerated. The adversarial
    # gate is the real discriminator; this only rejects far-worse-than-quadratic.
    assert gu.within_one_tier(label, "O(n^2)"), (
        f"soft complexity: estimated {label} is more than one tier above O(n^2); "
        "strong signal of a wrong (super-quadratic) algorithm."
    )


# ---------------------------------------------------------------------------
# 12. Advisory code-quality report (never asserted)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
