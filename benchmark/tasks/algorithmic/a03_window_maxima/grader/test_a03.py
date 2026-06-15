"""Grader for algorithmic/a03_window_maxima.  Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test layers (per RUBRIC.md §algorithmic):
  1. Correctness (>=8 cases): happy path, boundaries, edge cases, adversarial.
  2. Complexity hard gate: N=1_000_000, k=1_000, timeout=5.0 s via gu.run_within.
  3. Complexity soft signal: gu.estimate_time_complexity + gu.within_one_tier.
  4. Advisory code quality report (never asserted).
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a03_window_maxima"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
window_maxima = gu.load_callable(SOL, "solution.py", "window_maxima")

# ---------------------------------------------------------------------------
# Helper: brute-force reference for small inputs
# ---------------------------------------------------------------------------

def _naive(nums: list[int], k: int) -> list[int]:
    """O(n*k) reference — only used on tiny inputs."""
    return [max(nums[i : i + k]) for i in range(len(nums) - k + 1)]


# ---------------------------------------------------------------------------
# Correctness tests (>=8 required for algorithmic tasks)
# ---------------------------------------------------------------------------

def test_k_equals_1():
    """k=1: every element is its own window maximum."""
    nums = [4, -1, 7, 0, 3]
    assert window_maxima(nums, 1) == nums


def test_k_equals_len():
    """k==len(nums): single window spanning the whole list."""
    nums = [2, 8, 1, 5, -3]
    assert window_maxima(nums, len(nums)) == [max(nums)]


def test_known_example():
    """Classic textbook example from TASK.md."""
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    expected = [3, 3, 5, 5, 6, 7]
    assert window_maxima(nums, 3) == expected


def test_decreasing_sequence():
    """Strictly decreasing: the first element of each window is always the max."""
    nums = [10, 9, 8, 7, 6, 5]
    k = 3
    expected = _naive(nums, k)
    assert window_maxima(nums, k) == expected


def test_increasing_sequence():
    """Strictly increasing: the last element of each window is always the max."""
    nums = [1, 2, 3, 4, 5, 6]
    k = 3
    expected = _naive(nums, k)
    assert window_maxima(nums, k) == expected


def test_all_duplicates():
    """All equal values: every window max should equal that value."""
    nums = [7] * 10
    k = 4
    assert window_maxima(nums, k) == [7] * (len(nums) - k + 1)


def test_mixed_with_duplicates():
    """Mix of repeated and unique values."""
    nums = [3, 3, 1, 3, 3, 3, 2, 2]
    k = 4
    expected = _naive(nums, k)
    assert window_maxima(nums, k) == expected


def test_negative_numbers():
    """All negative values — result should also be negative."""
    nums = [-5, -3, -8, -1, -7]
    k = 2
    expected = _naive(nums, k)
    assert window_maxima(nums, k) == expected


def test_single_element_window_k1():
    """Single element list with k=1."""
    assert window_maxima([42], 1) == [42]


def test_k_greater_than_len_returns_empty():
    """k > len(nums) must return []."""
    assert window_maxima([1, 2, 3], 5) == []
    assert window_maxima([], 1) == []


def test_k_zero_raises_value_error():
    """k=0 must raise ValueError."""
    with pytest.raises(ValueError):
        window_maxima([1, 2, 3], 0)


def test_k_negative_raises_value_error():
    """Negative k must raise ValueError."""
    with pytest.raises(ValueError):
        window_maxima([1, 2, 3], -1)


def test_result_length():
    """Output length must equal len(nums) - k + 1 for valid k."""
    nums = list(range(20))
    for k in range(1, 21):
        result = window_maxima(nums, k)
        assert len(result) == len(nums) - k + 1, f"wrong length for k={k}"


def test_adversarial_max_at_left_edge():
    """Maximum sits at index 0; older deque entries must be properly expired."""
    nums = [100] + list(range(50))
    k = 10
    expected = _naive(nums, k)
    assert window_maxima(nums, k) == expected


# ---------------------------------------------------------------------------
# Complexity hard gate  (the real discriminator between O(n) and O(n*k))
# ---------------------------------------------------------------------------

def test_large_input_within_time_limit():
    """N=1_000_000, k=1_000 must finish within 5 s — fails O(n*k) implementations."""
    rng = random.Random(42)
    n, k = 1_000_000, 1_000
    nums = [rng.randint(-10**6, 10**6) for _ in range(n)]

    # Compute reference with the naive approach on a small prefix to cross-check.
    prefix = nums[:5000]
    prefix_k = 100
    prefix_ref = _naive(prefix, prefix_k)

    # Run the candidate on the full input under the time budget.
    result = gu.run_within(5.0, window_maxima, nums, k)

    assert len(result) == n - k + 1, "wrong output length on large input"

    # Spot-check the first window and one window mid-way through.
    assert result[0] == max(nums[:k]), "first window maximum is wrong"
    mid = n // 2
    assert result[mid] == max(nums[mid : mid + k]), "mid-point window maximum is wrong"

    # Verify prefix with naive (proves correctness, not just termination).
    prefix_result = window_maxima(prefix, prefix_k)
    assert prefix_result == prefix_ref, "prefix spot-check failed"


# ---------------------------------------------------------------------------
# Complexity soft signal (only fails if >2 tiers worse than O(n))
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity_linear():
    """Empirical curve fit should classify the candidate as roughly O(n)."""
    rng = random.Random(0)
    sizes = [5_000, 10_000, 20_000, 50_000, 100_000, 200_000]
    k_fixed = 50  # fixed k so only n varies

    def make_input(n: int):
        return ([rng.randint(-1000, 1000) for _ in range(n)], k_fixed)

    def run(payload):
        nums, k = payload
        window_maxima(nums, k)

    timings = gu.measure_runtime(make_input, run, sizes, repeats=3)
    report = gu.estimate_time_complexity(timings)
    print(f"soft_complexity: {report}")

    target = "O(n)"
    measured = report["label"]
    assert gu.within_one_tier(measured, target), (
        f"complexity estimate {measured!r} is more than one tier worse than {target!r}; "
        f"full report: {report}"
    )


# ---------------------------------------------------------------------------
# Advisory code quality (never a pass/fail gate)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted
