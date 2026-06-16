"""Grader for algorithmic/a09_interval_stab. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference
(the broken treats closed intervals as half-open, so touching intervals are
over-counted).
"""
from __future__ import annotations

import random
from itertools import combinations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a09_interval_stab"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
min_stabbing_points = gu.load_callable(SOL, "solution.py", "min_stabbing_points")


def _brute(intervals):
    """Independent reference: minimum hitting set over candidate points = the right
    endpoints (provably sufficient for interval stabbing). Exponential — small n only."""
    if not intervals:
        return 0
    cands = sorted({b for _, b in intervals})
    for k in range(1, len(cands) + 1):
        for combo in combinations(cands, k):
            if all(any(a <= p <= b for p in combo) for a, b in intervals):
                return k
    return len(cands)


def test_empty():
    assert min_stabbing_points([]) == 0


def test_single():
    assert min_stabbing_points([(5, 7)]) == 1


def test_nested_one_point():
    assert min_stabbing_points([(1, 10), (3, 4)]) == 1


def test_disjoint():
    assert min_stabbing_points([(1, 2), (5, 6), (9, 10)]) == 3


def test_touching_two_intervals():
    # CLOSED intervals: [1,2] and [2,3] share the point 2 -> ONE point.
    assert min_stabbing_points([(1, 2), (2, 3)]) == 1


def test_touching_chain():
    # [0,1],[1,2],[2,3],[3,4] -> points at 1 and 3 -> 2.
    assert min_stabbing_points([(0, 1), (1, 2), (2, 3), (3, 4)]) == 2


def test_unsorted_input():
    ivs = [(8, 9), (1, 3), (2, 5), (9, 12)]
    assert min_stabbing_points(ivs) == _brute(ivs)


def test_overlapping_cluster_plus_outlier():
    ivs = [(1, 4), (2, 6), (5, 7), (100, 101)]
    assert min_stabbing_points(ivs) == _brute(ivs)


def test_random_small_vs_brute():
    rng = random.Random(2026)
    for _ in range(60):
        n = rng.randint(1, 7)
        ivs = []
        for _ in range(n):
            a = rng.randint(0, 12)
            b = a + rng.randint(0, 6)
            ivs.append((a, b))
        assert min_stabbing_points(ivs) == _brute(ivs), ivs


def test_all_identical():
    assert min_stabbing_points([(3, 5)] * 6) == 1


def test_medium_runs_fast():
    """Light O(n log n) sanity (not a hard gate): a quadratic solution would lag."""
    rng = random.Random(7)
    ivs = []
    for _ in range(40000):
        a = rng.randint(0, 1_000_000)
        ivs.append((a, a + rng.randint(0, 1000)))
    result = gu.run_within(5.0, min_stabbing_points, ivs)
    assert isinstance(result, int) and 1 <= result <= 40000


@pytest.mark.code_quality
def test_code_quality():
    print("code_quality:", gu.code_quality_report(SOL))
