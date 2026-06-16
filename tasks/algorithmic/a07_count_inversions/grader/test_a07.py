"""Grader for algorithmic/a07_count_inversions. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test catalogue (>=8 required for algorithmic):
  1.  test_empty               — empty list -> 0
  2.  test_single              — single element -> 0
  3.  test_sorted_ascending    — sorted ascending -> 0
  4.  test_sorted_descending   — sorted descending (distinct) -> n*(n-1)/2
  5.  test_duplicates_no_inv   — all duplicates -> 0
  6.  test_duplicates_mixed    — mixed with duplicates (equal pairs not counted)
  7.  test_mixed_small         — small mixed array, verified by O(n^2) reference
  8.  test_negatives           — negative values
  9.  test_large_values        — very large integer values
  10. test_no_mutation         — input list must not be mutated
  11. test_reference_check     — broader random array vs O(n^2) reference
  12. test_time_gate           — n=200000, must complete within 5 seconds (O(n^2) times out)
  13. test_soft_complexity     — empirical curve fit (soft, only fails >2 tiers off)
  14. test_code_quality        — advisory only (never asserted)
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a07_count_inversions"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
count_inversions = gu.load_callable(SOL, "solution.py", "count_inversions")

# Fixed seed for all random data — grader must be deterministic.
_RNG = random.Random(42)


def _reference(nums: list[int]) -> int:
    """O(n^2) reference implementation for small inputs."""
    count = 0
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] > nums[j]:
                count += 1
    return count


# ---------------------------------------------------------------------------
# 1-2  Empty / single-element boundary cases
# ---------------------------------------------------------------------------

def test_empty():
    assert count_inversions([]) == 0


def test_single():
    assert count_inversions([42]) == 0


# ---------------------------------------------------------------------------
# 3-4  Sorted arrays: 0 inversions (ascending) and n*(n-1)/2 (descending)
# ---------------------------------------------------------------------------

def test_sorted_ascending():
    assert count_inversions([1, 2, 3, 4, 5]) == 0


def test_sorted_descending():
    n = 6
    nums = list(range(n, 0, -1))  # [6, 5, 4, 3, 2, 1]
    expected = n * (n - 1) // 2   # 15
    assert count_inversions(nums) == expected


# ---------------------------------------------------------------------------
# 5-6  Duplicates: equal pairs must NOT count as inversions
# ---------------------------------------------------------------------------

def test_duplicates_no_inv():
    assert count_inversions([1, 1, 1, 1]) == 0


def test_duplicates_mixed():
    # [3, 1, 2, 1]: inversions are (3,1), (3,2), (3,1), (2,1) = 4
    nums = [3, 1, 2, 1]
    assert count_inversions(nums) == _reference(nums)


# ---------------------------------------------------------------------------
# 7  Small mixed array — exact reference check
# ---------------------------------------------------------------------------

def test_mixed_small():
    cases = [
        [2, 4, 1, 3],    # 3 inversions: (2,1),(4,1),(4,3)
        [3, 1, 2],        # 2 inversions: (3,1),(3,2)
        [1, 3, 2, 3, 1],  # several inversions
        [5, 4, 3, 2, 1],  # 10 inversions
    ]
    for nums in cases:
        expected = _reference(nums)
        assert count_inversions(nums) == expected, (
            f"count_inversions({nums}) should be {expected}"
        )


# ---------------------------------------------------------------------------
# 8  Negative values
# ---------------------------------------------------------------------------

def test_negatives():
    cases = [
        [-3, -1, -2],   # (-1,-2): 1 inversion
        [-5, -3, -4],   # (-3,-4): 1 inversion
        [-1, 0, 1],     # 0 inversions
        [1, -1, 0],     # (1,-1),(1,0): 2 inversions
    ]
    for nums in cases:
        expected = _reference(nums)
        assert count_inversions(nums) == expected, (
            f"count_inversions({nums}) should be {expected}"
        )


# ---------------------------------------------------------------------------
# 9  Very large integer values
# ---------------------------------------------------------------------------

def test_large_values():
    nums = [10**15, -(10**15), 0, 10**15 - 1, -(10**15) + 1]
    expected = _reference(nums)
    assert count_inversions(nums) == expected


# ---------------------------------------------------------------------------
# 10  No mutation: input list must not be modified
# ---------------------------------------------------------------------------

def test_no_mutation():
    nums = [5, 3, 1, 4, 2]
    original = list(nums)
    count_inversions(nums)
    assert nums == original, "count_inversions must not mutate the input list"


# ---------------------------------------------------------------------------
# 11  Broader random check vs O(n^2) reference
# ---------------------------------------------------------------------------

def test_reference_check():
    """Multiple random arrays of moderate size validated against O(n^2) reference."""
    rng = random.Random(99)
    for _ in range(10):
        n = rng.randint(10, 200)
        nums = [rng.randint(-1000, 1000) for _ in range(n)]
        expected = _reference(nums)
        got = count_inversions(nums)
        assert got == expected, (
            f"Mismatch for list of length {n}: got {got}, expected {expected}"
        )


# ---------------------------------------------------------------------------
# 12  HARD time gate: O(n^2) must time out; O(n log n) finishes with headroom
# ---------------------------------------------------------------------------

def test_time_gate():
    """n=200000 — an O(n log n) solution completes within 5 s; O(n^2) times out."""
    rng = random.Random(12345)
    nums = [rng.randint(-10**9, 10**9) for _ in range(200_000)]
    result = gu.run_within(5.0, count_inversions, nums)
    assert isinstance(result, int)
    assert result >= 0


# ---------------------------------------------------------------------------
# 13  SOFT complexity signal (only fails if >2 tiers worse than O(n log n))
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    """Empirical time-complexity estimate — advisory; only fails if egregiously wrong.

    Sizes are kept small enough that even an O(n^2) implementation can finish
    each sub-run quickly; the hard gate (test_time_gate) is what truly rejects
    slow implementations.
    """
    sizes = [200, 400, 800, 1500, 2500, 4000]

    def make_input(n: int) -> list[int]:
        rng = random.Random(n)
        return [rng.randint(-10**6, 10**6) for _ in range(n)]

    timings = gu.measure_runtime(make_input, count_inversions, sizes)
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n log n)  ranked={report['ranked'][:4]}")
    assert gu.within_one_tier(label, "O(n log n)"), (
        f"soft complexity check: estimated {label} is more than one tier above O(n log n). "
        "This is a strong signal of an incorrect or inefficient algorithm."
    )


# ---------------------------------------------------------------------------
# 14  Advisory code-quality report (never asserted)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)   # advisory only — never a gate
