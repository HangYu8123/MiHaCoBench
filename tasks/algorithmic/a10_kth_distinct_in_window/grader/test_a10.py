"""Grader for algorithmic/a10_kth_distinct_in_window. Public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Ground truth is an INDEPENDENT O(n*w) brute force (``_brute``) that rebuilds each
window's distinct set with ``sorted(set(...))``. The broken reference uses
``distinct > k`` instead of ``distinct >= k``, so it returns ``None`` on windows
with exactly ``k`` distinct values; the exact-k and random tests catch this, while
the time gate is passed by both (broken is still the efficient algorithm).

Test catalogue (>=8 required for algorithmic):
  1.  test_singleton_window           — w=1
  2.  test_full_array_window          — w=n, single window
  3.  test_worked_example             — spelled-out cases from TASK.md
  4.  test_exact_k_boundary           — windows with exactly k distinct (discriminator)
  5.  test_fewer_than_k_is_none       — windows with < k distinct -> None
  6.  test_all_equal                  — single distinct value
  7.  test_random_small_vs_brute      — many random inputs vs brute
  8.  test_adversarial_vs_brute       — heavy duplicates / negatives / wide k
  9.  test_exceptions                 — w<1,k<1 -> ValueError; w>n -> []
  10. test_time_gate                  — n=200000, w=1000, timeout 5s (the real gate)
  11. test_soft_complexity            — empirical curve fit (advisory)
  12. test_code_quality               — advisory only (never asserted)
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a10_kth_distinct_in_window"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
kth_distinct_in_window = gu.load_callable(SOL, "solution.py", "kth_distinct_in_window")


def _brute(a: list[int], w: int, k: int) -> list:
    n = len(a)
    if w > n:
        return []
    out: list = []
    for i in range(n - w + 1):
        distinct = sorted(set(a[i:i + w]))
        out.append(distinct[k - 1] if len(distinct) >= k else None)
    return out


# ---------------------------------------------------------------------------
# 1. Window of width 1.
# ---------------------------------------------------------------------------

def test_singleton_window():
    a = [5, 7, 5, 9]
    assert kth_distinct_in_window(a, 1, 1) == [5, 7, 5, 9]
    assert kth_distinct_in_window(a, 1, 2) == [None, None, None, None]


# ---------------------------------------------------------------------------
# 2. Whole array as one window.
# ---------------------------------------------------------------------------

def test_full_array_window():
    a = [4, 1, 4, 2, 1]  # distinct sorted [1,2,4]
    assert kth_distinct_in_window(a, 5, 1) == [1]
    assert kth_distinct_in_window(a, 5, 2) == [2]
    assert kth_distinct_in_window(a, 5, 3) == [4]
    assert kth_distinct_in_window(a, 5, 4) == [None]


# ---------------------------------------------------------------------------
# 3. Worked examples from TASK.md.
# ---------------------------------------------------------------------------

def test_worked_example():
    assert kth_distinct_in_window([3, 1, 2, 1, 3], 3, 2) == [2, 2, 2]
    assert kth_distinct_in_window([1, 2, 3, 1, 2, 3], 3, 3) == [3, 3, 3, 3]


# ---------------------------------------------------------------------------
# 4. Exact-k boundary — windows with exactly k distinct must yield a value.
#    This is the discriminator vs the broken (> k) variant.
# ---------------------------------------------------------------------------

def test_exact_k_boundary():
    # Every window has exactly 2 distinct values.
    a = [1, 1, 2, 2, 1, 1]
    got = kth_distinct_in_window(a, 4, 2)
    assert got == _brute(a, 4, 2)
    assert None not in got, "exactly-k-distinct windows must NOT be None"
    # The [1,2,3,1,2,3]/w=3/k=3 case: all windows exactly 3 distinct.
    assert kth_distinct_in_window([1, 2, 3, 1, 2, 3], 3, 3) == [3, 3, 3, 3]


# ---------------------------------------------------------------------------
# 5. Fewer than k distinct -> None.
# ---------------------------------------------------------------------------

def test_fewer_than_k_is_none():
    a = [7, 7, 7, 8, 8]
    # windows of width 2: [7,7]->1 distinct, [7,7]->1, [7,8]->2, [8,8]->1
    assert kth_distinct_in_window(a, 2, 2) == [None, None, 8, None]


# ---------------------------------------------------------------------------
# 6. All-equal array.
# ---------------------------------------------------------------------------

def test_all_equal():
    a = [3] * 6
    assert kth_distinct_in_window(a, 3, 1) == [3, 3, 3, 3]
    assert kth_distinct_in_window(a, 3, 2) == [None, None, None, None]


# ---------------------------------------------------------------------------
# 7. Many random small inputs vs brute.
# ---------------------------------------------------------------------------

def test_random_small_vs_brute():
    rng = random.Random(2026)
    for _ in range(400):
        n = rng.randint(1, 25)
        a = [rng.randint(0, 6) for _ in range(n)]   # small alphabet -> many exact-k windows
        w = rng.randint(1, n)
        k = rng.randint(1, 6)
        assert kth_distinct_in_window(a, w, k) == _brute(a, w, k), f"a={a} w={w} k={k}"


# ---------------------------------------------------------------------------
# 8. Adversarial: heavy duplicates, negatives, wide k.
# ---------------------------------------------------------------------------

def test_adversarial_vs_brute():
    rng = random.Random(99)
    for _ in range(200):
        n = rng.randint(2, 30)
        a = [rng.choice([-5, -5, 0, 0, 0, 3, 7, 7, 100]) for _ in range(n)]
        w = rng.randint(1, n)
        k = rng.randint(1, 5)
        assert kth_distinct_in_window(a, w, k) == _brute(a, w, k), f"a={a} w={w} k={k}"


# ---------------------------------------------------------------------------
# 9. Exception / boundary contract.
# ---------------------------------------------------------------------------

def test_exceptions():
    with pytest.raises(ValueError):
        kth_distinct_in_window([1, 2, 3], 0, 1)
    with pytest.raises(ValueError):
        kth_distinct_in_window([1, 2, 3], 2, 0)
    assert kth_distinct_in_window([1, 2], 5, 1) == []  # w > n


# ---------------------------------------------------------------------------
# 10. ADVERSARIAL hard time gate: n=200000, w=1000, timeout 5s.
# ---------------------------------------------------------------------------

@pytest.mark.adversarial
def test_time_gate():
    """n=200000, w=1000, must return within 5s.

    The O(n log V) gold finishes well under a second. A naive per-window rebuild
    of the distinct set is O(n*w) ~ 2e8 and cannot.
    """
    n = 200_000
    w = 1000
    k = 10
    rng = random.Random(42)
    a = [rng.randint(0, 5000) for _ in range(n)]

    result = gu.run_within(5.0, kth_distinct_in_window, a, w, k)
    assert isinstance(result, list)
    assert len(result) == n - w + 1

    # Spot-check the same construction on a small instance against brute.
    rng2 = random.Random(42)
    small = [rng2.randint(0, 5000) for _ in range(200)]
    assert kth_distinct_in_window(small, 50, 10) == _brute(small, 50, 10)


# ---------------------------------------------------------------------------
# 11. SOFT complexity signal (advisory).
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    sizes = [2000, 4000, 8000, 16000, 32000]

    def make_input(n: int):
        rng = random.Random(n)
        a = [rng.randint(0, 500) for _ in range(n)]
        return (a, 100, 5)

    timings = gu.measure_runtime(
        make_input,
        lambda args: kth_distinct_in_window(args[0], args[1], args[2]),
        sizes,
        repeats=2,
    )
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n log V)  ranked={report['ranked'][:3]}")
    assert gu.within_one_tier(label, "O(n^2)"), (
        f"soft complexity check: estimated {label} is more than one tier above O(n^2)."
    )


# ---------------------------------------------------------------------------
# 12. Advisory code-quality report (never asserted).
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
