"""Grader for competitive/cp05_kth_subarray_sum. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference is an O(n^2) enumerate-and-sort brute force: it is CORRECT
on every small case but TIMES OUT on the hard complexity gate (n=120000, 8s), so
the gate test is the unambiguous discriminator.

Test catalogue (>=10 required for competitive):
  1.  test_singleton              — n=1, k=1 -> a[0]
  2.  test_all_equal              — all-equal array, exact ranks
  3.  test_k_equals_one_minimum   — k=1 returns min(a)
  4.  test_k_equals_max_total     — k=max returns sum(a)
  5.  test_known_small_case       — fully spelled-out multiset vs brute
  6.  test_random_small_vs_brute  — many random small cases vs brute reference
  7.  test_with_zeros             — non-negative array containing zeros
  8.  test_duplicate_sums_ties    — every rank across a tie-heavy array vs brute
  9.  test_adversarial_clustered  — adversarial value distribution vs brute
  10. test_full_rank_sweep        — sweep ALL k from 1..n(n+1)/2 vs brute
  11. test_adversarial_time_gate  — n=120000, fixed-seed, timeout 8s (the real gate)
  12. test_soft_complexity        — empirical curve fit (soft, fails only >2 tiers off)
  13. test_code_quality           — advisory only (never asserted)
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "competitive", "cp05_kth_subarray_sum"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
kth_subarray_sum = gu.load_callable(SOL, "solution.py", "kth_subarray_sum")


# ---------------------------------------------------------------------------
# Independent reference: O(n^2) brute force — enumerate ALL contiguous-subarray
# sums, sort, index the k-th smallest (1-indexed). Correct; used for SMALL n only.
# ---------------------------------------------------------------------------

def _brute_kth(a: list[int], k: int) -> int:
    """Enumerate every contiguous-subarray sum, sort, return the k-th smallest."""
    n = len(a)
    sums: list[int] = []
    for i in range(n):
        running = 0
        for j in range(i, n):
            running += a[j]
            sums.append(running)
    sums.sort()
    return sums[k - 1]


# ---------------------------------------------------------------------------
# 1. Singleton — only one subarray exists, k must be 1.
# ---------------------------------------------------------------------------

def test_singleton():
    assert kth_subarray_sum([7], 1) == 7
    assert kth_subarray_sum([0], 1) == 0


# ---------------------------------------------------------------------------
# 2. All-equal array — exact known ranks.
# ---------------------------------------------------------------------------

def test_all_equal():
    # a = [2, 2, 2]; sorted sums = [2, 2, 2, 4, 4, 6]
    a = [2, 2, 2]
    for k, exp in [(1, 2), (3, 2), (4, 4), (5, 4), (6, 6)]:
        assert kth_subarray_sum(a, k) == exp == _brute_kth(a, k)


# ---------------------------------------------------------------------------
# 3. k = 1 returns the minimum element (smallest possible subarray sum).
# ---------------------------------------------------------------------------

def test_k_equals_one_minimum():
    a = [5, 2, 9, 4, 7]
    assert kth_subarray_sum(a, 1) == min(a)
    assert kth_subarray_sum(a, 1) == _brute_kth(a, 1)


# ---------------------------------------------------------------------------
# 4. k = max returns the total sum (largest subarray sum is the whole array).
# ---------------------------------------------------------------------------

def test_k_equals_max_total():
    a = [5, 2, 9, 4, 7]
    n = len(a)
    k_max = n * (n + 1) // 2
    assert kth_subarray_sum(a, k_max) == sum(a)
    assert kth_subarray_sum(a, k_max) == _brute_kth(a, k_max)


# ---------------------------------------------------------------------------
# 5. Known small case — fully spelled-out multiset, checked against brute.
# ---------------------------------------------------------------------------

def test_known_small_case():
    # a = [1, 2, 3]; subarray sums = {1, 3, 6, 2, 5, 3} -> sorted [1, 2, 3, 3, 5, 6]
    a = [1, 2, 3]
    expected_sorted = [1, 2, 3, 3, 5, 6]
    for k in range(1, len(expected_sorted) + 1):
        got = kth_subarray_sum(a, k)
        assert got == expected_sorted[k - 1], f"k={k}: got {got}"
        assert got == _brute_kth(a, k)


# ---------------------------------------------------------------------------
# 6. Many random small cases vs the independent brute reference.
# ---------------------------------------------------------------------------

def test_random_small_vs_brute():
    rng = random.Random(2026)
    for _ in range(400):
        n = rng.randint(1, 14)
        a = [rng.randint(0, 12) for _ in range(n)]
        total_ranks = n * (n + 1) // 2
        k = rng.randint(1, total_ranks)
        got = kth_subarray_sum(a, k)
        exp = _brute_kth(a, k)
        assert got == exp, f"a={a}, k={k}: got {got}, expected {exp}"


# ---------------------------------------------------------------------------
# 7. Non-negative array containing zeros.
# ---------------------------------------------------------------------------

def test_with_zeros():
    # a = [0, 0, 5]; sums = [0,0,5,0,5,5] -> sorted [0,0,0,5,5,5]
    a = [0, 0, 5]
    for k, exp in [(1, 0), (3, 0), (4, 5), (6, 5)]:
        assert kth_subarray_sum(a, k) == exp == _brute_kth(a, k)
    # Trailing/embedded zeros at scale (small) vs brute, every rank.
    b = [0, 3, 0, 0, 4, 0]
    n = len(b)
    for k in range(1, n * (n + 1) // 2 + 1):
        assert kth_subarray_sum(b, k) == _brute_kth(b, k), f"zeros k={k}"


# ---------------------------------------------------------------------------
# 8. Tie-heavy array — every rank across a multiset full of duplicate sums.
#    Catches any candidate that deduplicates equal sums.
# ---------------------------------------------------------------------------

def test_duplicate_sums_ties():
    a = [1, 1, 1, 1, 1, 1]  # sums are 1,2,3,4,5,6 with high multiplicity
    n = len(a)
    for k in range(1, n * (n + 1) // 2 + 1):
        got = kth_subarray_sum(a, k)
        exp = _brute_kth(a, k)
        assert got == exp, f"ties k={k}: got {got}, expected {exp}"


# ---------------------------------------------------------------------------
# 9. Adversarial clustered/skewed value distribution (mix of 0s and big spikes).
#    A wrong count predicate (off-by-one or non-monotone handling) diverges here.
# ---------------------------------------------------------------------------

def test_adversarial_clustered():
    rng = random.Random(99)
    for _ in range(120):
        n = rng.randint(2, 18)
        a = []
        for _ in range(n):
            # Heavy mix of zeros and occasional large spikes -> many ties and gaps.
            a.append(0 if rng.random() < 0.5 else rng.randint(900, 1000))
        total_ranks = n * (n + 1) // 2
        # Probe a spread of ranks including the boundaries.
        ks = {1, total_ranks, total_ranks // 2, max(1, total_ranks // 4),
              min(total_ranks, 3 * total_ranks // 4)}
        for k in ks:
            got = kth_subarray_sum(a, k)
            exp = _brute_kth(a, k)
            assert got == exp, f"a={a}, k={k}: got {got}, expected {exp}"


# ---------------------------------------------------------------------------
# 10. Full-rank sweep on a fixed medium array — every k from 1..n(n+1)/2.
# ---------------------------------------------------------------------------

def test_full_rank_sweep():
    rng = random.Random(7)
    a = [rng.randint(0, 50) for _ in range(40)]
    n = len(a)
    total_ranks = n * (n + 1) // 2
    for k in range(1, total_ranks + 1):
        got = kth_subarray_sum(a, k)
        exp = _brute_kth(a, k)
        assert got == exp, f"sweep k={k}: got {got}, expected {exp}"


# ---------------------------------------------------------------------------
# 11. ADVERSARIAL hard time gate: n=120000, fixed seed, timeout=8s.
#     This is the real complexity discriminator.
# ---------------------------------------------------------------------------

@pytest.mark.adversarial
def test_adversarial_time_gate():
    """n=120000 non-negative array (fixed seed), middle k, must finish within 8s.

    The O(n log(totalSum)) gold finishes in well under a second (>=3x headroom).
    The O(n^2) enumerate-and-sort would enumerate ~7.2e9 subarray sums (many
    minutes, tens of GB) and TIMES OUT here.
    """
    n = 120_000
    rng = random.Random(42)
    a = [rng.randint(0, 1000) for _ in range(n)]
    k = (n * (n + 1) // 2) // 2

    result = gu.run_within(8.0, kth_subarray_sum, a, k)

    # Sanity: a single non-negative int within the valid value range.
    assert isinstance(result, int)
    assert 0 <= result <= sum(a)

    # Spot-check the same construction on a small instance against brute.
    n_small = 60
    rng2 = random.Random(42)
    a_small = [rng2.randint(0, 1000) for _ in range(n_small)]
    k_small = (n_small * (n_small + 1) // 2) // 2
    assert kth_subarray_sum(a_small, k_small) == _brute_kth(a_small, k_small)


# ---------------------------------------------------------------------------
# 12. SOFT complexity signal (advisory; fails only if >2 tiers worse than O(n)).
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    """Empirical time-complexity estimate -- advisory only.

    Sizes are kept small so even an O(n^2) submission completes during the grader
    run; the hard gate (test_adversarial_time_gate) is the real discriminator.
    The target is O(n log(totalSum)) ~ O(n log n); we allow up to O(n^2) (two
    tiers above O(n)) before failing, so only an algo far worse than quadratic is
    flagged here.
    """
    sizes = [500, 1000, 2000, 4000, 8000]

    def make_input(n: int):
        rng = random.Random(n)
        a = [rng.randint(0, 1000) for _ in range(n)]
        k = (n * (n + 1) // 2) // 2
        return (a, k)

    timings = gu.measure_runtime(
        make_input,
        lambda args: kth_subarray_sum(args[0], args[1]),
        sizes,
        repeats=2,
    )
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n log n)  ranked={report['ranked'][:3]}")
    assert gu.within_one_tier(label, "O(n^2)"), (
        f"soft complexity check: estimated {label} is more than one tier above "
        "O(n^2) — a strong signal of a wrong (worse-than-quadratic) algorithm."
    )


# ---------------------------------------------------------------------------
# 13. Advisory code-quality report (never asserted).
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
