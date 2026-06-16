"""Grader for debug/dbg06_interval_merge. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold (fixed) reference, FAILS on the broken
(still-buggy) reference. The FAIL_TO_PASS tests probe the two planted bugs
(touching intervals not merged, and unsorted input handled incorrectly); the
PASS_TO_PASS tests guard the behaviour the buggy code already handles correctly
(overlap, empty, single, nested, clearly-disjoint sorted).
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "debug", "dbg06_interval_merge"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
merge_intervals = gu.load_callable(SOL, "solution.py", "merge_intervals")


# ---- FAIL_TO_PASS: the planted bugs ---------------------------------------- #

def test_touching_intervals_merged():
    """Two intervals sharing an endpoint must become one — the primary symptom."""
    result = merge_intervals([(1, 3), (3, 5)])
    assert result == [(1, 5)]


def test_chain_of_touching_intervals():
    """A chain of touching intervals must collapse into a single interval."""
    result = merge_intervals([(0, 1), (1, 2), (2, 3)])
    assert result == [(0, 3)]


def test_unsorted_input_merged_correctly():
    """Input not sorted by start — the hidden second defect."""
    result = merge_intervals([(3, 6), (1, 4)])
    assert result == [(1, 6)]


def test_mixed_overlap_and_touch_unsorted():
    """Mix of overlapping and touching on unsorted input."""
    result = merge_intervals([(5, 8), (1, 3), (3, 5)])
    assert result == [(1, 8)]


def test_touching_at_zero():
    """Touching at zero boundary."""
    result = merge_intervals([(0, 0), (0, 1)])
    assert result == [(0, 1)]


def test_unsorted_non_overlapping_ordered_correctly():
    """Unsorted disjoint intervals must be returned in sorted order."""
    result = merge_intervals([(10, 20), (1, 5)])
    assert result == [(1, 5), (10, 20)]


# ---- PASS_TO_PASS: behaviour the buggy code already handles ---------------- #

def test_empty_input():
    result = merge_intervals([])
    assert result == []


def test_single_interval():
    result = merge_intervals([(2, 7)])
    assert result == [(2, 7)]


def test_clearly_disjoint_sorted_unchanged():
    """Non-overlapping, non-touching sorted intervals pass through unchanged."""
    result = merge_intervals([(1, 2), (4, 6), (8, 10)])
    assert result == [(1, 2), (4, 6), (8, 10)]


def test_overlapping_intervals_merged():
    """Clearly overlapping intervals (strict overlap) are merged."""
    result = merge_intervals([(1, 5), (3, 8)])
    assert result == [(1, 8)]


def test_fully_nested_interval():
    """One interval wholly contained in another merges to the outer."""
    result = merge_intervals([(1, 10), (3, 6)])
    assert result == [(1, 10)]


def test_point_interval_touching():
    """A zero-length (point) interval that touches an adjacent interval."""
    result = merge_intervals([(2, 5), (5, 5)])
    assert result == [(2, 5)]


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
