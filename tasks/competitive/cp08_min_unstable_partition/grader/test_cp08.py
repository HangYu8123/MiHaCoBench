"""Grader for competitive/cp08_min_unstable_partition. Public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Ground truth is an INDEPENDENT brute force (``_brute``) that enumerates ALL
2^(n-1) partitions on small inputs, keeps the valid ones with the minimum segment
count, and returns the lexicographically-smallest end-index list among them. This
shares no structure with the gold's reach/minseg/binary-search approach.

The broken reference uses greedy-farthest cutting: it gets the minimum COUNT right
but returns lexicographically-LARGEST ends, so every test that pins the actual
cut list (not just the count) discriminates it.

Test catalogue (>=10 required for competitive):
  1.  test_singleton                 — n=1 -> [0]
  2.  test_all_equal                 — one segment [n-1]
  3.  test_strictly_increasing_k0    — every element its own segment
  4.  test_worked_example            — [1,2,3,4],K=2 -> [0,3] (and != greedy [2,3])
  5.  test_lex_beats_greedy_cases    — hand cases where lex-smallest != greedy-far
  6.  test_random_small_vs_brute     — many random inputs vs brute
  7.  test_adversarial_vs_brute      — clustered / wide-range inputs vs brute
  8.  test_returned_partition_valid  — result is valid AND minimal count (vs brute)
  9.  test_time_gate                 — n=100000, fixed seed, timeout 4s (the real gate)
  10. test_soft_complexity           — empirical curve fit (advisory)
  11. test_code_quality              — advisory only (never asserted)
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "competitive", "cp08_min_unstable_partition"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
min_unstable_cuts = gu.load_callable(SOL, "solution.py", "min_unstable_cuts")


# ---------------------------------------------------------------------------
# Independent reference: enumerate all 2^(n-1) partitions. SMALL n only.
# Returns (min_count, lex_smallest_ends).
# ---------------------------------------------------------------------------

def _brute(values: list[int], K: int):
    n = len(values)
    if n == 0:
        return (0, [])
    best_count = None
    best_ends = None
    for mask in range(1 << (n - 1)):
        ends = []
        start = 0
        ok = True
        for p in range(n - 1):
            if (mask >> p) & 1:
                seg = values[start:p + 1]
                if max(seg) - min(seg) > K:
                    ok = False
                    break
                ends.append(p)
                start = p + 1
        if not ok:
            continue
        seg = values[start:n]
        if max(seg) - min(seg) > K:
            continue
        ends.append(n - 1)
        cnt = len(ends)
        if best_count is None or cnt < best_count or (cnt == best_count and ends < best_ends):
            best_count = cnt
            best_ends = ends
    return (best_count, best_ends)


def _segments_valid(values: list[int], K: int, ends: list[int]) -> bool:
    start = 0
    for e in ends:
        seg = values[start:e + 1]
        if not seg or max(seg) - min(seg) > K:
            return False
        start = e + 1
    return start == len(values) and ends == sorted(ends) and len(set(ends)) == len(ends)


# ---------------------------------------------------------------------------
# 1. Singleton.
# ---------------------------------------------------------------------------

def test_singleton():
    assert min_unstable_cuts([5], 0) == [0]
    assert min_unstable_cuts([5], 10) == [0]


# ---------------------------------------------------------------------------
# 2. All equal -> one segment.
# ---------------------------------------------------------------------------

def test_all_equal():
    assert min_unstable_cuts([3, 3, 3, 3], 0) == [3]
    assert min_unstable_cuts([7, 7, 7], 5) == [2]


# ---------------------------------------------------------------------------
# 3. Strictly increasing with K=0 -> every element its own segment.
# ---------------------------------------------------------------------------

def test_strictly_increasing_k0():
    assert min_unstable_cuts([1, 2, 3, 4, 5], 0) == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# 4. Worked example from TASK.md — gold [0,3], greedy/broken [2,3].
# ---------------------------------------------------------------------------

def test_worked_example():
    got = min_unstable_cuts([1, 2, 3, 4], 2)
    assert got == [0, 3]
    assert got != [2, 3]  # the greedy-farthest (broken) answer
    cnt, ends = _brute([1, 2, 3, 4], 2)
    assert got == ends and len(got) == cnt


# ---------------------------------------------------------------------------
# 5. Hand cases where lex-smallest differs from greedy-farthest.
# ---------------------------------------------------------------------------

def test_lex_beats_greedy_cases():
    cases = [
        ([1, 2, 3, 4, 5, 6], 2),
        ([5, 4, 3, 2, 1], 2),
        ([0, 1, 2, 0, 1, 2], 1),
        ([10, 11, 12, 13, 14], 2),
        ([1, 1, 2, 2, 3, 3], 1),
    ]
    for values, K in cases:
        cnt, ends = _brute(values, K)
        got = min_unstable_cuts(values, K)
        assert got == ends, f"values={values} K={K}: got {got}, expected {ends}"


# ---------------------------------------------------------------------------
# 6. Many random small inputs vs brute.
# ---------------------------------------------------------------------------

def test_random_small_vs_brute():
    rng = random.Random(2026)
    for _ in range(400):
        n = rng.randint(1, 13)
        values = [rng.randint(0, 8) for _ in range(n)]
        K = rng.randint(0, 8)
        cnt, ends = _brute(values, K)
        got = min_unstable_cuts(values, K)
        assert got == ends, f"values={values} K={K}: got {got}, expected {ends}"


# ---------------------------------------------------------------------------
# 7. Adversarial distributions vs brute.
# ---------------------------------------------------------------------------

def test_adversarial_vs_brute():
    rng = random.Random(99)
    for _ in range(200):
        n = rng.randint(2, 13)
        # Wide range + occasional spikes -> rich set of feasible cut points.
        values = [rng.choice([0, 1, 2, 50, 51, 100]) for _ in range(n)]
        K = rng.choice([0, 1, 2, 49, 50, 100])
        cnt, ends = _brute(values, K)
        got = min_unstable_cuts(values, K)
        assert got == ends, f"values={values} K={K}: got {got}, expected {ends}"


# ---------------------------------------------------------------------------
# 8. Returned partition is valid AND uses the minimum segment count.
# ---------------------------------------------------------------------------

def test_returned_partition_valid():
    rng = random.Random(7)
    for _ in range(150):
        n = rng.randint(1, 13)
        values = [rng.randint(0, 10) for _ in range(n)]
        K = rng.randint(0, 10)
        got = min_unstable_cuts(values, K)
        assert _segments_valid(values, K, got), f"invalid partition {got} for {values}, K={K}"
        cnt, _ = _brute(values, K)
        assert len(got) == cnt, f"non-minimal: {len(got)} segments, min is {cnt}"


# ---------------------------------------------------------------------------
# 9. ADVERSARIAL hard time gate: n=100000, fixed seed, timeout 4s.
# ---------------------------------------------------------------------------

@pytest.mark.adversarial
def test_time_gate():
    """n=100000, must return within 4s.

    The O(n log n) gold finishes well under a second. An O(n^2) feasibility
    recompute (re-deriving each candidate segment's max-min) cannot.
    """
    n = 100_000
    rng = random.Random(42)
    values = [rng.randint(0, 1000) for _ in range(n)]
    K = 100

    result = gu.run_within(4.0, min_unstable_cuts, values, K)
    assert isinstance(result, list)
    assert result and result[-1] == n - 1
    assert _segments_valid(values, K, result)

    # Spot-check the same construction on a small instance against brute.
    rng2 = random.Random(42)
    vs = [rng2.randint(0, 1000) for _ in range(12)]
    cnt, ends = _brute(vs, 100)
    assert min_unstable_cuts(vs, 100) == ends


# ---------------------------------------------------------------------------
# 10. SOFT complexity signal (advisory).
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    sizes = [1000, 2000, 4000, 8000, 16000]

    def make_input(n: int):
        rng = random.Random(n)
        values = [rng.randint(0, 1000) for _ in range(n)]
        return (values, 100)

    timings = gu.measure_runtime(
        make_input,
        lambda args: min_unstable_cuts(args[0], args[1]),
        sizes,
        repeats=2,
    )
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n log n)  ranked={report['ranked'][:3]}")
    assert gu.within_one_tier(label, "O(n^2)"), (
        f"soft complexity check: estimated {label} is more than one tier above O(n^2)."
    )


# ---------------------------------------------------------------------------
# 11. Advisory code-quality report (never asserted).
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
