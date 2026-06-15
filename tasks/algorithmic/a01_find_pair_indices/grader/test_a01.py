"""Grader for algorithmic/a01_find_pair_indices. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test plan
---------
Correctness (>=8 hard tests):
  1. basic pair
  2. no pair -> None
  3. negative numbers
  4. zeros
  5. duplicate values
  6. tiebreak: smallest-j selection
  7. tiebreak: smallest-i for same j
  8. empty list -> None
  9. single element -> None
 10. pair only at the very end

Complexity (hard gate):
 11. 2_000_000-element input, answer near the end, must finish within 5.0 s

Complexity (soft signal):
 12. @pytest.mark.soft_complexity — empirical curve fit; only fails if >2 tiers worse than O(n)

Advisory:
 13. @pytest.mark.code_quality — prints code_quality_report, never asserts
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a01_find_pair_indices"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
find = gu.load_callable(SOL, "solution.py", "find_pair_indices")


# ---------------------------------------------------------------------------
# Correctness tests
# ---------------------------------------------------------------------------

def test_basic_pair():
    """Simple case: one clear pair."""
    result = find([2, 7, 11, 15], 9)
    assert result == (0, 1)


def test_no_pair_returns_none():
    """No two elements sum to target."""
    result = find([1, 2, 3, 4], 100)
    assert result is None


def test_negative_numbers():
    """Pair involving negative integers."""
    result = find([-3, 1, 5, -1, 4], 1)
    # -3 + 4 = 1 at indices (0, 4); also 1 + ? No: we want smallest j.
    # j=1: need 0, not in seen={-3:0}. No.
    # j=2: need -4, not in seen. No.
    # j=3: need 2, not in seen. No.
    # j=4: need -3, in seen -> (0, 4)
    assert result == (0, 4)


def test_zeros():
    """Pair of zeros summing to zero."""
    result = find([0, 1, 0, 2], 0)
    # j=2: complement=0, seen={0:0,1:1} -> (0,2)
    assert result == (0, 2)


def test_duplicate_values():
    """Duplicates: ensure indices are used correctly, not values."""
    result = find([3, 3, 3, 7], 6)
    # j=1: complement=3, seen={3:0} -> (0,1)
    assert result == (0, 1)


def test_tiebreak_smallest_j():
    """Multiple valid j values — must return the one with smallest j."""
    # [1, 5, 3, 4] target=8: pairs are (1,3) sum=1+7? No.
    # Let's construct clearly: [2, 6, 1, 7] target=8
    # j=1: complement=2, seen={2:0} -> pair (0,1). That's smallest j=1.
    result = find([2, 6, 1, 7], 8)
    assert result == (0, 1)


def test_tiebreak_smallest_i_for_same_j():
    """For the winning j, must return the smallest valid i."""
    # [1, 3, 5, 4] target=9 -> first hit: j=2, complement=4 not in {1,3}.
    #   j=3, complement=5, seen={1:0,3:1,5:2} -> (2,3). Only one i for j=3.
    # To test smallest-i: need same j with multiple possible i's is tricky in
    # a single-pass left-to-right scan because seen stores only first occurrence.
    # [2, 2, 8] target=10: j=2, complement=8 not present. No hit.
    # Better: [3, 1, 3, 7] target=10 -> j=3, complement=3, seen has 3 at index 0 -> (0,3).
    # The pair (2,3) also sums to 10 but i=0 < i=2, so correct answer is (0,3).
    result = find([3, 1, 3, 7], 10)
    assert result == (0, 3)


def test_empty_list_returns_none():
    """Empty input must return None."""
    assert find([], 5) is None


def test_single_element_returns_none():
    """Single element cannot form a pair."""
    assert find([42], 84) is None


def test_pair_at_very_end():
    """Pair only at the last two positions of the list."""
    nums = [99] * 998 + [1, 9]
    # No pair among 99s (99+99=198 != 10). First pair: index 998+999=10.
    result = find(nums, 10)
    assert result == (998, 999)


# ---------------------------------------------------------------------------
# Hard complexity gate
# ---------------------------------------------------------------------------

def test_large_input_within_time():
    """2_000_000-element input with the answer near the end; must finish in 5 s.

    An O(n^2) implementation takes ~thousands of seconds and times out.
    """
    n = 2_000_000
    # Build a list of zeros; place the answer pair near the end.
    # nums = [0] * (n-2) + [3, 7], target = 10
    # Expected pair: (n-2, n-1)
    nums = [0] * (n - 2) + [3, 7]
    target = 10
    result = gu.run_within(5.0, find, nums, target)
    assert result == (n - 2, n - 1)


# ---------------------------------------------------------------------------
# Soft complexity signal
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity_linear():
    """Empirical curve fit — fails only if >2 tiers worse than O(n).

    Sizes are kept small (max 4000) so this test completes quickly for both
    O(n) and O(n^2) implementations within the grader time budget.
    """
    sizes = [500, 1_000, 2_000, 4_000, 8_000]

    def make_input(n):
        # Answer near the end to exercise the full scan.
        return ([0] * (n - 2) + [1, 9], 10)

    def run(payload):
        nums, target = payload
        find(nums, target)

    timings = gu.measure_runtime(make_input, run, sizes, repeats=3)
    result = gu.estimate_time_complexity(timings)
    print(f"soft_complexity: estimated={result['label']} residuals={result['residuals']}")
    measured_idx = gu.COMPLEXITY_ORDER.index(result["label"])
    target_idx = gu.COMPLEXITY_ORDER.index("O(n)")
    assert measured_idx <= target_idx + 2, (
        f"Complexity estimated as {result['label']}, which is more than 2 tiers "
        f"worse than O(n). Full residuals: {result['residuals']}"
    )


# ---------------------------------------------------------------------------
# Advisory code-quality report
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
