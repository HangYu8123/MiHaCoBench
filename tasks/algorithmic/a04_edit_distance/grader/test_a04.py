"""Grader for algorithmic/a04_edit_distance. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Test catalogue (≥8 required for algorithmic):
  1.  test_identical            — distance is 0 for equal strings
  2.  test_empty_vs_nonempty    — one empty string → distance = len(other)
  3.  test_nonempty_vs_empty    — reversed direction
  4.  test_both_empty           — distance is 0
  5.  test_single_substitution  — "a" vs "b"
  6.  test_single_insertion     — "a" vs "ab"
  7.  test_single_deletion      — "ab" vs "a"
  8.  test_kitten_sitting       — classic example (distance 3)
  9.  test_sunday_saturday      — classic example (distance 3)
  10. test_symmetry             — edit_distance(a,b) == edit_distance(b,a)
  11. test_unicode              — multi-byte characters count as single chars
  12. test_time_gate            — 2000-char strings, must complete within 8 s
  13. test_space_gate           -- 1000-char strings, peak heap < 5 MB
  14. test_soft_complexity      — empirical curve fit (soft, only fails >2 tiers off)
  15. test_code_quality         — advisory only (never asserted)
"""
from __future__ import annotations

import random
import string

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "algorithmic", "a04_edit_distance"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
edit_distance = gu.load_callable(SOL, "solution.py", "edit_distance")

# Fixed seed for all random data — grader must be deterministic.
_RNG = random.Random(42)


# ---------------------------------------------------------------------------
# 1-4  Trivial / boundary cases
# ---------------------------------------------------------------------------

def test_identical():
    assert edit_distance("hello", "hello") == 0


def test_empty_vs_nonempty():
    assert edit_distance("", "abc") == 3


def test_nonempty_vs_empty():
    assert edit_distance("abc", "") == 3


def test_both_empty():
    assert edit_distance("", "") == 0


# ---------------------------------------------------------------------------
# 5-7  Single-edit cases
# ---------------------------------------------------------------------------

def test_single_substitution():
    assert edit_distance("a", "b") == 1


def test_single_insertion():
    assert edit_distance("a", "ab") == 1


def test_single_deletion():
    assert edit_distance("ab", "a") == 1


# ---------------------------------------------------------------------------
# 8-9  Classic examples
# ---------------------------------------------------------------------------

def test_kitten_sitting():
    # kitten → sitten (subst k→s), sitten → sittin (subst e→i), sittin → sitting (insert g)
    assert edit_distance("kitten", "sitting") == 3


def test_sunday_saturday():
    assert edit_distance("sunday", "saturday") == 3


# ---------------------------------------------------------------------------
# 10  Symmetry
# ---------------------------------------------------------------------------

def test_symmetry():
    pairs = [
        ("algorithm", "altruistic"),
        ("intention", "execution"),
        ("", "xyz"),
        ("abcde", "abcde"),
    ]
    for a, b in pairs:
        assert edit_distance(a, b) == edit_distance(b, a), \
            f"symmetry failed for ({a!r}, {b!r})"


# ---------------------------------------------------------------------------
# 11  Unicode
# ---------------------------------------------------------------------------

def test_unicode():
    # Each accented character or emoji is ONE edit unit.
    assert edit_distance("café", "cafe") == 1           # é → e : 1 substitution
    assert edit_distance("résumé", "resume") == 2       # two substitutions


# ---------------------------------------------------------------------------
# 12  HARD time gate: O(n^2) solution must finish; exponential would not.
# ---------------------------------------------------------------------------

def test_time_gate():
    """Strings of length 2000 — an O(m*n) solution completes, O(2^n) would not."""
    a = "".join(_RNG.choices(string.ascii_lowercase, k=2000))
    b = "".join(_RNG.choices(string.ascii_lowercase, k=2000))
    result = gu.run_within(8.0, edit_distance, a, b)
    # The result must be an int in the valid range [0, 2000].
    assert isinstance(result, int)
    assert 0 <= result <= 2000


# ---------------------------------------------------------------------------
# 13  HARD space gate: must be < 5 MB peak; a full O(m*n) table exceeds this.
# ---------------------------------------------------------------------------

def test_space_gate():
    """Peak tracemalloc allocation for 1000x1000 strings must be < 5 MB.

    A full (1001 x 1001) Python list-of-lists occupies roughly 36 MB due to
    list-of-lists pointer structure overhead; a rolling single-row approach
    stays under 100 KB.

    String length is kept at 1000 so both the correct (rolling) and broken
    (full 2-D table) solutions run to completion under tracemalloc without
    blowing the overall test-suite time budget.
    """
    a = "".join(_RNG.choices(string.ascii_lowercase, k=1000))
    b = "".join(_RNG.choices(string.ascii_lowercase, k=1000))
    peak_bytes = gu.measure_peak_memory(edit_distance, a, b)
    limit = 5_000_000  # 5 MB
    assert peak_bytes < limit, (
        f"peak heap {peak_bytes:,} bytes >= {limit:,} bytes; "
        "solution must use O(min(m,n)) space (rolling/single-row array), "
        "not a full O(m*n) table"
    )


# ---------------------------------------------------------------------------
# 14  SOFT complexity signal (only fails if >2 tiers worse than O(n^2))
# ---------------------------------------------------------------------------

@pytest.mark.soft_complexity
def test_soft_complexity():
    """Empirical time-complexity estimate -- advisory; only fails if egregiously wrong."""
    sizes = [100, 200, 400, 700, 1000, 1400]

    def make_input(n):
        rng = random.Random(n)
        return (
            "".join(rng.choices(string.ascii_lowercase, k=n)),
            "".join(rng.choices(string.ascii_lowercase, k=n)),
        )

    timings = gu.measure_runtime(make_input, lambda pair: edit_distance(*pair), sizes)
    report = gu.estimate_time_complexity(timings)
    label = report["label"]
    print(f"[soft_complexity] estimated={label}  target=O(n^2)  ranked={report['ranked'][:3]}")
    assert gu.within_one_tier(label, "O(n^2)"), (
        f"soft complexity check: estimated {label} is more than one tier above O(n^2). "
        "This is a very strong signal of an incorrect algorithm."
    )


# ---------------------------------------------------------------------------
# 15  Advisory code-quality report (never asserted)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)   # advisory only — never a gate
