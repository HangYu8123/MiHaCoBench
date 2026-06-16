"""Grader for algorithmic/a06_sliding_window_median. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test layers (per RUBRIC.md §algorithmic):
  1. Correctness (>=8 cases): k==1, k==len, single element, duplicates,
     negatives, even-k average, all-equal, classic example, adversarial.
  2. Complexity hard gate: N=200_000, k=1_000, timeout=8.0 s via gu.run_within.
     An O(n*k) re-sort-each-window approach times out; the O(n log k) gold passes.
  3. Complexity soft signal: gu.estimate_time_complexity + gu.within_one_tier.
  4. Advisory code quality report (never asserted).
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a06_sliding_window_median"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
sliding_window_median = gu.load_callable(SOL, "solution.py", "sliding_window_median")


# ---------------------------------------------------------------------------
# Helper: brute-force reference for small inputs
# ---------------------------------------------------------------------------

def _naive(nums: list[float], k: int) -> list[float]:
    """O(n*k log k) reference — only used on tiny inputs for cross-checking."""
    result = []
    n = len(nums)
    for i in range(n - k + 1):
        window = sorted(nums[i : i + k])
        if k % 2 == 1:
            result.append(float(window[k // 2]))
        else:
            result.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return result


def _check(nums: list[float], k: int) -> None:
    """Assert that the candidate matches the naive reference for a small input."""
    expected = _naive(nums, k)
    actual = sliding_window_median(nums, k)
    assert len(actual) == len(expected), (
        f"length mismatch: got {len(actual)}, expected {len(expected)}"
    )
    for idx, (a, e) in enumerate(zip(actual, expected)):
        assert gu.close(a, e), (
            f"window {idx}: got {a}, expected {e} (nums={nums}, k={k})"
        )


# ---------------------------------------------------------------------------
# Correctness tests (>=8 required for algorithmic tasks)
# ---------------------------------------------------------------------------

def test_k_equals_1():
    """k=1: every element is its own single-element window; median == element."""
    nums = [4.0, -1.0, 7.0, 0.0, 3.0]
    result = sliding_window_median(nums, 1)
    assert len(result) == len(nums)
    for a, e in zip(result, nums):
        assert gu.close(a, e)


def test_k_equals_len():
    """k==len(nums): single window spanning the whole list."""
    nums = [2.0, 8.0, 1.0, 5.0, -3.0]
    result = sliding_window_median(nums, len(nums))
    assert len(result) == 1
    assert gu.close(result[0], _naive(nums, len(nums))[0])


def test_single_element_list():
    """Singleton list with k=1."""
    result = sliding_window_median([42.0], 1)
    assert len(result) == 1
    assert gu.close(result[0], 42.0)


def test_k_greater_than_len_returns_empty():
    """k > len(nums) must return []."""
    assert sliding_window_median([1.0, 2.0, 3.0], 5) == []
    assert sliding_window_median([], 1) == []


def test_k_zero_raises_value_error():
    """k=0 must raise ValueError."""
    with pytest.raises(ValueError):
        sliding_window_median([1.0, 2.0, 3.0], 0)


def test_k_negative_raises_value_error():
    """Negative k must raise ValueError."""
    with pytest.raises(ValueError):
        sliding_window_median([1.0, 2.0, 3.0], -1)


def test_odd_k_classic_example():
    """Classic example from TASK.md with odd k=3."""
    nums = [1.0, 3.0, -1.0, -3.0, 5.0, 3.0, 6.0, 7.0]
    expected = [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]
    result = sliding_window_median(nums, 3)
    assert len(result) == len(expected)
    for a, e in zip(result, expected):
        assert gu.close(a, e)


def test_even_k_average():
    """Even k: median is the average of the two middle values."""
    nums = [1.0, 2.0, 3.0, 4.0]
    expected = [1.5, 2.5, 3.5]
    result = sliding_window_median(nums, 2)
    assert len(result) == len(expected)
    for a, e in zip(result, expected):
        assert gu.close(a, e)


def test_even_k_larger_window():
    """Even k=4 example."""
    nums = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    _check(nums, 4)


def test_all_equal():
    """All equal values: every window median should equal that value."""
    nums = [7.0] * 10
    k = 4
    result = sliding_window_median(nums, k)
    assert len(result) == len(nums) - k + 1
    for a in result:
        assert gu.close(a, 7.0)


def test_duplicates():
    """Mix of repeated and unique values."""
    nums = [3.0, 3.0, 1.0, 3.0, 3.0, 3.0, 2.0, 2.0]
    _check(nums, 4)


def test_negative_numbers():
    """All-negative values — result should also be negative."""
    nums = [-5.0, -3.0, -8.0, -1.0, -7.0, -2.0]
    _check(nums, 3)


def test_float_values():
    """Floating-point input values (not just integers)."""
    nums = [1.5, 2.5, 0.5, 3.5, 2.0]
    _check(nums, 3)


def test_result_length():
    """Output length must equal len(nums) - k + 1 for valid k."""
    nums = list(range(20))
    for k in range(1, 21):
        result = sliding_window_median(nums, k)
        assert len(result) == len(nums) - k + 1, f"wrong length for k={k}"


def test_adversarial_max_at_left_edge():
    """Maximum/minimum values at the left edge; old entries must expire correctly."""
    nums = [100.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    _check(nums, 5)


def test_adversarial_random_medium():
    """Random medium-sized array; compare against naive reference."""
    rng = random.Random(999)
    nums = [float(rng.randint(-50, 50)) for _ in range(200)]
    for k in [3, 5, 10, 20]:
        _check(nums, k)


# ---------------------------------------------------------------------------
# Complexity hard gate  (the real discriminator between O(n log k) and O(n*k))
# ---------------------------------------------------------------------------

def test_large_input_within_time_limit():
    """N=200_000, k=1_000 must finish within 8 s — fails O(n*k) implementations."""
    rng = random.Random(42)
    n, k = 200_000, 1_000
    nums = [float(rng.randint(-10**6, 10**6)) for _ in range(n)]

    result = gu.run_within(8.0, sliding_window_median, nums, k)

    assert len(result) == n - k + 1, "wrong output length on large input"

    # Spot-check a small prefix against the naive solution.
    prefix_len = 500
    prefix_k = 50
    prefix_nums = nums[:prefix_len]
    prefix_ref = _naive(prefix_nums, prefix_k)
    prefix_result = sliding_window_median(prefix_nums, prefix_k)
    assert len(prefix_result) == len(prefix_ref)
    for a, e in zip(prefix_result, prefix_ref):
        assert gu.close(a, e), f"prefix spot-check failed: got {a}, expected {e}"

    # Spot-check first and a mid window.
    first_window_ref = _naive(nums[:k], k)[0]
    assert gu.close(result[0], first_window_ref), (
        f"first window median wrong: got {result[0]}, expected {first_window_ref}"
    )
    mid = n // 2
    mid_ref = _naive(nums[mid : mid + k], k)[0]
    assert gu.close(result[mid], mid_ref), (
        f"mid-point window median wrong: got {result[mid]}, expected {mid_ref}"
    )


# ---------------------------------------------------------------------------
# Complexity soft signal (only fails if >2 tiers worse than O(n log n))
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    """Empirical curve fit should classify the candidate as roughly O(n log n) or better."""
    rng = random.Random(0)
    sizes = [5_000, 10_000, 20_000, 50_000, 100_000]
    k_fixed = 100  # fixed k so only n varies

    def make_input(n: int):
        return ([float(rng.randint(-1000, 1000)) for _ in range(n)], k_fixed)

    def run(payload):
        nums, k = payload
        sliding_window_median(nums, k)

    timings = gu.measure_runtime(make_input, run, sizes, repeats=3)
    report = gu.estimate_time_complexity(timings)
    print(f"soft_complexity: {report}")

    target = "O(n log n)"
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
