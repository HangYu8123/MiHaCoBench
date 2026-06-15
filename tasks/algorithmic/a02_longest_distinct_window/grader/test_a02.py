"""Grader for algorithmic/a02_longest_distinct_window.

Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test plan (>=8 for algorithmic category):
  1. test_empty           — empty list -> 0
  2. test_singleton       — [x] -> 1
  3. test_all_same        — [v,v,v,...] -> 1
  4. test_all_distinct    — [1,2,3,4] -> 4
  5. test_mixed_basic     — simple mixed case
  6. test_window_reset    — window must correctly reset on second occurrence
  7. test_longer_case     — [1,2,3,1,2,3,4,5] -> 5
  8. test_two_elements_dup — [3, 3] -> 1
  9. test_adversarial_pattern — alternating values (short windows)
 10. test_large_input_gate  — N=1_000_000, hard O(n) timing gate (HARD)
 11. test_soft_complexity   — empirical curve-fit (SOFT, only fails if >2 tiers worse)
 12. test_code_quality      — advisory, never asserted
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a02_longest_distinct_window"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
fn = gu.load_callable(SOL, "solution.py", "longest_distinct_window")


# ---------------------------------------------------------------------------
# Correctness tests (≥8 required by RUBRIC.md)
# ---------------------------------------------------------------------------

def test_empty():
    """Empty list returns 0."""
    assert fn([]) == 0


def test_singleton():
    """Single element returns 1."""
    assert fn([42]) == 1


def test_all_same():
    """All identical elements: longest window is 1."""
    assert fn([7, 7, 7, 7, 7]) == 1


def test_all_distinct():
    """All distinct: longest window is the full list."""
    seq = [1, 2, 3, 4, 5]
    assert fn(seq) == len(seq)


def test_mixed_basic():
    """Simple mixed case: [1,2,1,3,2,4] -> 4 ([1,3,2,4] or [2,1,3,2] etc.)."""
    # Best window: starting at index 1 -> [2,1,3,2] no, that has dup 2.
    # Actually [1,3,2,4] from index 2 onward = length 4.
    assert fn([1, 2, 1, 3, 2, 4]) == 4


def test_window_reset_correctly():
    """Window must jump past old duplicate, not just shrink by one."""
    # [1,2,3,1,2,3]: when second 1 appears at index 3, left moves to 1 (not 0+1).
    # Best: [1,2,3] length 3, then [2,3,1] at idx 1-3 (wait: 3 appears at 2,3 is next=5?)
    # seq = [1,2,3,1,2,3]: windows [0..2]=3, [1..3]=3 ([2,3,1]), [2..4]=3 ([3,1,2]), ...
    # All length-3; answer is 3.
    assert fn([1, 2, 3, 1, 2, 3]) == 3


def test_longer_case():
    """[1,2,3,1,2,3,4,5] -> best window is [1,2,3,4,5] = length 5."""
    assert fn([1, 2, 3, 1, 2, 3, 4, 5]) == 5


def test_two_element_dup():
    """Two identical elements returns 1."""
    assert fn([3, 3]) == 1


def test_two_element_distinct():
    """Two distinct elements returns 2."""
    assert fn([3, 4]) == 2


def test_adversarial_alternating():
    """Alternating pattern [0,1,0,1,...]: longest window is 2."""
    seq = [i % 2 for i in range(100)]
    assert fn(seq) == 2


def test_large_distinct_prefix():
    """Long run of distinct values followed by a duplicate."""
    # [0,1,2,...,999,0]: answer is 1000 (the prefix [0..999]).
    seq = list(range(1000)) + [0]
    assert fn(seq) == 1000


# ---------------------------------------------------------------------------
# Hard complexity gate: N=1_000_000, must finish within 5.0 seconds.
# An O(n^2) broken solution cannot pass this; the gold O(n) solution can.
# ---------------------------------------------------------------------------

def test_large_input_gate():
    """Hard gate: N=1,000,000. O(n^2) broken solution times out."""
    n = 1_000_000
    # Pattern: [0,1,2,...,999,0,1,2,...,999,...] — window size cycles at 1000.
    # Answer = 1000 (repeating block of 1000 distinct values).
    cycle = 1000
    seq = [i % cycle for i in range(n)]
    expected = cycle  # longest window with all distinct = 1000

    result = gu.run_within(5.0, fn, seq)
    assert result == expected, f"expected {expected}, got {result}"


# ---------------------------------------------------------------------------
# Soft complexity signal (fails only if >2 tiers worse than O(n))
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    """Soft signal: empirical fit should be approximately O(n) or better."""
    import math

    sizes = [500, 1000, 2000, 4000, 8000, 16000, 32000]

    def make_input(n: int):
        # Mix of distinct and repeating; window resets every 500 elements.
        cycle = 500
        return [i % cycle for i in range(n)]

    timings = gu.measure_runtime(make_input, fn, sizes, repeats=3)
    result = gu.estimate_time_complexity(timings)
    measured = result["label"]
    target = "O(n)"
    # Fail only if measured is more than 2 tiers worse than O(n).
    assert gu.within_one_tier(measured, target) or (
        gu.COMPLEXITY_ORDER.index(measured) <= gu.COMPLEXITY_ORDER.index(target) + 2
    ), (
        f"Complexity appears to be {measured!r}, which is more than 2 tiers "
        f"worse than target {target!r}. Ranked: {result['ranked']}"
    )
    print(f"[soft_complexity] measured={measured!r}, target={target!r}, "
          f"ranked={result['ranked']}")


# ---------------------------------------------------------------------------
# Advisory code-quality report (never a pass/fail gate)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only: print code quality metrics, never assert."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
