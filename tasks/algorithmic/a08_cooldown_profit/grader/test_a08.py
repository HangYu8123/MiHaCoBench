"""Grader for algorithmic/a08_cooldown_profit. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test catalogue (>=8 required for algorithmic):
  1.  test_empty                       — no jobs -> 0
  2.  test_single                      — one job -> its profit
  3.  test_two_overlapping             — overlapping pair -> the better one
  4.  test_gap_boundary_selectable     — two jobs separated by EXACTLY gap -> both
  5.  test_gap_boundary_one_short      — separated by gap-1 -> only the better one
  6.  test_zero_profit                 — zero-profit jobs never hurt
  7.  test_adversarial_greedy_cluster  — cluster of small jobs beats one big job
                                         (defeats profit-descending greedy)
  8.  test_reference_random_small      — many random small cases vs O(n^2) DP reference
  9.  test_no_mutation                 — input list/tuples must not be mutated
  10. test_time_gate                   — N=200000 jobs, must finish within 6 s
                                         (a naive O(n^2) DP times out)
  11. test_soft_complexity             — empirical curve fit (soft, only fails >2 tiers off)
  12. test_code_quality                — advisory only (never asserted)
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a08_cooldown_profit"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
max_profit = gu.load_callable(SOL, "solution.py", "max_profit")

# Fixed seed for all random data — grader must be deterministic.
_RNG = random.Random(42)


# ---------------------------------------------------------------------------
# Independent O(n^2) DP reference (correct but slow) for SMALL inputs only.
# ---------------------------------------------------------------------------

def _reference(jobs: list[tuple], gap: int) -> int:
    """Independent O(n^2) DP: structurally different from the gold's binary search.

    Sort by end; dp[i] = best profit using jobs[0..i] with job i chosen last is
    folded into a running best. We compute best[i] = max profit over the first i
    jobs (end-sorted) by scanning all earlier jobs for a feasible predecessor.
    """
    if not jobs:
        return 0
    ordered = sorted(jobs, key=lambda j: (j[1], j[0], j[2]))
    n = len(ordered)
    # take[i] = best total profit of a selection ending exactly with job i.
    take = [0] * n
    answer = 0
    for i in range(n):
        s_i, _e_i, p_i = ordered[i]
        best_prev = 0
        for k in range(i):
            _s_k, e_k, _p_k = ordered[k]
            if e_k <= s_i - gap:           # job k may precede job i (cooldown)
                if take[k] > best_prev:
                    best_prev = take[k]
        take[i] = best_prev + p_i
        if take[i] > answer:
            answer = take[i]
    return answer


# ---------------------------------------------------------------------------
# 1-2  Empty / single-element boundary cases
# ---------------------------------------------------------------------------

def test_empty():
    assert max_profit([], 0) == 0
    assert max_profit([], 5) == 0


def test_single():
    assert max_profit([(0, 10, 7)], 0) == 7
    assert max_profit([(3, 8, 42)], 100) == 42


# ---------------------------------------------------------------------------
# 3  Two overlapping jobs -> only the better one is selectable
# ---------------------------------------------------------------------------

def test_two_overlapping():
    # [0,10) and [5,15) overlap -> pick the higher profit.
    assert max_profit([(0, 10, 5), (5, 15, 9)], 0) == 9
    assert max_profit([(0, 10, 12), (5, 15, 9)], 0) == 12


# ---------------------------------------------------------------------------
# 4-5  Cooldown boundary: separated by EXACTLY gap (both) vs gap-1 (only one)
# ---------------------------------------------------------------------------

def test_gap_boundary_selectable():
    # First job ends at 10; second starts at 13; gap = 3 -> 10 + 3 == 13, both OK.
    jobs = [(0, 10, 5), (13, 20, 6)]
    assert max_profit(jobs, 3) == 11   # both chosen
    # Reference agrees.
    assert _reference(jobs, 3) == 11


def test_gap_boundary_one_short():
    # First job ends at 10; second starts at 13; gap = 4 -> need start >= 14,
    # but start is 13 -> cannot take both, so only the better single job.
    jobs = [(0, 10, 5), (13, 20, 6)]
    assert max_profit(jobs, 4) == 6    # only the better one
    assert _reference(jobs, 4) == 6


# ---------------------------------------------------------------------------
# 6  Zero-profit jobs never reduce the optimum
# ---------------------------------------------------------------------------

def test_zero_profit():
    jobs = [(0, 10, 0), (10, 20, 0), (20, 30, 5)]
    assert max_profit(jobs, 0) == 5
    assert _reference(jobs, 0) == 5


# ---------------------------------------------------------------------------
# 7  ADVERSARIAL: a cluster of small-profit jobs beats one big-profit job.
#    A profit-descending greedy grabs the single big job and is BLOCKED from the
#    whole cluster -> it returns 10; the optimum (gold) is 15.
# ---------------------------------------------------------------------------

def test_adversarial_greedy_cluster():
    big = (0, 100, 10)
    cluster = [
        (0, 10, 3),
        (10, 20, 3),
        (20, 30, 3),
        (30, 40, 3),
        (40, 50, 3),
    ]
    jobs = [big] + cluster
    # Optimal: the 5 small jobs (each abutting the next, gap=0) total 15 > 10.
    assert max_profit(jobs, 0) == 15
    # Sanity: the independent reference agrees with the gold's claimed optimum.
    assert _reference(jobs, 0) == 15

    # A second, larger adversarial instance with a cooldown so the win margin is
    # unambiguous and order-insensitive.
    big2 = (0, 1000, 50)
    cluster2 = [(i * 20, i * 20 + 10, 8) for i in range(20)]  # 20 jobs, gap 10 fits
    jobs2 = cluster2 + [big2]
    expected2 = _reference(jobs2, 10)
    assert max_profit(jobs2, 10) == expected2
    assert expected2 > 50   # the cluster must beat the single big job


# ---------------------------------------------------------------------------
# 8  Random small cases validated against the independent O(n^2) reference.
# ---------------------------------------------------------------------------

def test_reference_random_small():
    rng = random.Random(99)
    for _ in range(120):
        n = rng.randint(0, 18)
        jobs = []
        for _ in range(n):
            s = rng.randint(0, 40)
            dur = rng.randint(1, 12)
            p = rng.randint(0, 20)
            jobs.append((s, s + dur, p))
        gap = rng.randint(0, 6)
        expected = _reference(jobs, gap)
        got = max_profit(jobs, gap)
        assert got == expected, (
            f"mismatch for jobs={jobs}, gap={gap}: got {got}, expected {expected}"
        )


# ---------------------------------------------------------------------------
# 9  No mutation: the input list (and tuples) must be left untouched.
# ---------------------------------------------------------------------------

def test_no_mutation():
    jobs = [(0, 10, 5), (12, 20, 6), (3, 7, 4)]
    snapshot = [tuple(j) for j in jobs]
    max_profit(jobs, 2)
    assert jobs == snapshot, "max_profit must not mutate its input"


# ---------------------------------------------------------------------------
# 10  HARD time gate: O(n log n) finishes with headroom; a naive O(n^2) DP
#     (~4e10 ops at N=2e5) cannot finish in time.
# ---------------------------------------------------------------------------

def test_time_gate():
    """N=200000 jobs — an O(n log n) solution completes within 6 s; O(n^2) times out."""
    rng = random.Random(2026)
    n = 200_000
    jobs = []
    for _ in range(n):
        s = rng.randint(0, 5_000_000)
        dur = rng.randint(1, 50)
        p = rng.randint(0, 1000)
        jobs.append((s, s + dur, p))
    gap = 7
    result = gu.run_within(6.0, max_profit, jobs, gap)
    assert isinstance(result, int)
    assert result >= 0


# ---------------------------------------------------------------------------
# 11  SOFT complexity signal (only fails if >2 tiers worse than O(n log n))
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    """Empirical time-complexity estimate — advisory; only fails if egregiously wrong.

    Sizes are kept small enough that even a slow implementation finishes each
    sub-run; the hard gate (test_time_gate) is what truly rejects slow code.
    """
    sizes = [500, 1000, 2000, 4000, 8000, 16000]

    def make_input(n: int):
        rng = random.Random(n)
        jobs = []
        for _ in range(n):
            s = rng.randint(0, 1_000_000)
            dur = rng.randint(1, 40)
            jobs.append((s, s + dur, rng.randint(0, 500)))
        return jobs

    timings = gu.measure_runtime(make_input, lambda jobs: max_profit(jobs, 5), sizes)
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n log n)  ranked={report['ranked'][:4]}")
    assert gu.within_one_tier(label, "O(n log n)"), (
        f"soft complexity check: estimated {label} is more than one tier above O(n log n). "
        "This is a strong signal of an incorrect or inefficient algorithm."
    )


# ---------------------------------------------------------------------------
# 12  Advisory code-quality report (never asserted)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)   # advisory only — never a gate
