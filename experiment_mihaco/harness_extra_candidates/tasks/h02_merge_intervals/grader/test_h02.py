"""Grader for harness/h02_merge_intervals.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference uses a STRICT overlap test (``start < running_end``) instead
of the half-open adjacency rule (``start <= running_end``). So genuinely
overlapping/nested intervals still coalesce, but ADJACENT half-open intervals do
NOT: ``[(1, 3), (3, 5)]`` is wrongly left as two intervals instead of merging into
``[(1, 5)]``. The adjacency-merge and chain tests (and the independent-oracle
cases that contain adjacencies) kill this defect; the overlap/nested, gap,
exception, purity, empty/singleton, and zero-length-only tests still pass on the
broken variant.
"""
from __future__ import annotations

import copy

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h02_merge_intervals"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

merge = gu.load_callable(SOL, "solution.py", "merge")


# ---------------------------------------------------------------------------
# Independent oracle (lives in the GRADER, never imports the gold).
#
# This is a STRUCTURALLY DIFFERENT reconstruction of the answer than any
# sort-and-sweep merge: for INTEGER endpoints, expand each half-open interval
# [s, e) into the explicit set of covered integer points {s, s+1, ..., e-1},
# union them, then rebuild canonical maximal runs of consecutive integers. A run
# of integers p..q (inclusive) corresponds to the half-open interval (p, q + 1).
#
# Because it reasons over the literal point set, it bakes in the half-open
# semantics directly: a zero-length [s, s) contributes the empty set (dropped),
# and an adjacency [1, 3) + [3, 5) yields the contiguous integer run 1,2,3,4 ->
# (1, 5). It is only valid for INTEGER endpoints, so every oracle case below uses
# integer endpoints exclusively. It does NOT validate start > end (that is the
# function-under-test's job, exercised separately).
# ---------------------------------------------------------------------------
def _oracle(intervals):
    """Independent half-open coalescer for INTEGER-endpoint intervals only."""
    points: set[int] = set()
    for start, end in intervals:
        # Half-open: covers integers start .. end-1 (empty when start == end).
        for p in range(start, end):
            points.add(p)
    if not points:
        return []
    out: list[tuple[int, int]] = []
    run_start = run_prev = None
    for p in sorted(points):
        if run_start is None:
            run_start = run_prev = p
        elif p == run_prev + 1:
            run_prev = p
        else:
            # Gap in the integer points -> close the current maximal run.
            out.append((run_start, run_prev + 1))
            run_start = run_prev = p
    out.append((run_start, run_prev + 1))
    return out


# Self-test the oracle against the TASK.md worked examples (integer-endpoint
# subset) so we know the independent reference itself is trustworthy.
def test_oracle_self_consistency_on_worked_examples():
    assert _oracle([(1, 3), (3, 5)]) == [(1, 5)]
    assert _oracle([(1, 5), (2, 3)]) == [(1, 5)]
    assert _oracle([(5, 7), (1, 3)]) == [(1, 3), (5, 7)]
    assert _oracle([(1, 4), (2, 2), (4, 6)]) == [(1, 6)]
    assert _oracle([(0, 0)]) == []
    assert _oracle([]) == []


# Deterministic, committed oracle cases (INTEGER endpoints only). A mix of
# adjacency, overlap, nesting, duplicates, unsorted input, negatives, zero-length
# fillers, and gaps.
_ORACLE_CASES = [
    [],
    [(0, 0)],
    [(1, 3), (3, 5)],                       # adjacency
    [(0, 1), (1, 2), (2, 3)],               # adjacency chain
    [(1, 5), (2, 3)],                       # nested
    [(5, 7), (1, 3)],                       # gap, unsorted
    [(1, 4), (2, 2), (4, 6)],               # zero-length dropped + adjacency
    [(0, 2), (3, 3), (5, 7)],               # empty interval inside a gap
    [(10, 12), (11, 15), (14, 14), (3, 5)], # overlap + zero-length + gap, unsorted
    [(-5, -2), (-2, 0), (0, 1)],            # negatives with adjacency chain
    [(2, 4), (2, 4), (2, 4)],               # duplicates
    [(-3, 7), (-3, 7)],                     # duplicate single span
    [(7, 9), (1, 2), (4, 4), (3, 5), (8, 11)],  # several runs, unsorted, with a filler
]


# ---------------------------------------------------------------------------
# Test 1 [independent oracle]: merge(...) must equal the independent oracle on
# every committed integer-endpoint case. Adjacency-bearing cases here also kill
# the strict-overlap defect.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("case", _ORACLE_CASES)
def test_matches_independent_oracle(case):
    assert merge(list(case)) == _oracle(case), f"mismatch on {case}"


# ---------------------------------------------------------------------------
# Test 2 [FAIL_TO_PASS]: half-open adjacency merges. The strict-overlap defect
# leaves these as separate intervals.
# ---------------------------------------------------------------------------
def test_half_open_adjacency_merges():
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]
    # An adjacency chain must collapse to a single interval.
    assert merge([(0, 1), (1, 2), (2, 3)]) == [(0, 3)]


# ---------------------------------------------------------------------------
# Test 3 [FAIL_TO_PASS]: zero-length intervals are dropped.
# ---------------------------------------------------------------------------
def test_zero_length_dropped():
    # A lone empty interval yields nothing.
    assert merge([(2, 2)]) == []
    # An empty interval between two adjacency-merging intervals contributes
    # nothing (the (1,4) & (4,6) adjacency still merges).
    assert merge([(1, 4), (2, 2), (4, 6)]) == [(1, 6)]
    # An empty interval sitting inside a real gap is simply dropped; the gap
    # stays a gap.
    assert merge([(0, 2), (3, 3), (5, 7)]) == [(0, 2), (5, 7)]


# ---------------------------------------------------------------------------
# Test 4: overlapping and nested intervals coalesce (passes on broken too).
# ---------------------------------------------------------------------------
def test_overlap_and_nested():
    assert merge([(1, 5), (2, 3)]) == [(1, 5)]          # nested
    assert merge([(1, 4), (2, 6)]) == [(1, 6)]          # partial overlap
    assert merge([(1, 10), (2, 4), (3, 5), (6, 9)]) == [(1, 10)]  # all absorbed


# ---------------------------------------------------------------------------
# Test 5: a genuine gap is preserved and the output is sorted by start.
# ---------------------------------------------------------------------------
def test_gap_preserved_and_sorted():
    assert merge([(5, 7), (1, 3)]) == [(1, 3), (5, 7)]
    assert merge([(20, 25), (1, 4), (10, 12)]) == [(1, 4), (10, 12), (20, 25)]


# ---------------------------------------------------------------------------
# Test 6: duplicates and unsorted input.
# ---------------------------------------------------------------------------
def test_duplicates_and_unsorted():
    assert merge([(2, 4), (2, 4), (2, 4)]) == [(2, 4)]
    assert merge([(8, 11), (1, 2), (3, 5), (7, 9)]) == [(1, 2), (3, 5), (7, 11)]


# ---------------------------------------------------------------------------
# Test 7: negative coordinates (incl. an adjacency across zero) [FAIL_TO_PASS].
# ---------------------------------------------------------------------------
def test_negative_coordinates():
    assert merge([(-5, -2), (-2, 0), (0, 1)]) == [(-5, 1)]
    assert merge([(-10, -5), (-3, -1)]) == [(-10, -5), (-3, -1)]


# ---------------------------------------------------------------------------
# Test 8: single interval and empty input.
# ---------------------------------------------------------------------------
def test_single_and_empty():
    assert merge([(3, 8)]) == [(3, 8)]
    assert merge([]) == []
    # An input consisting solely of empty intervals collapses to nothing.
    assert merge([(2, 2), (5, 5), (-1, -1)]) == []


# ---------------------------------------------------------------------------
# Test 9: start > end raises ValueError; start == end is allowed (dropped).
# ---------------------------------------------------------------------------
def test_invalid_interval_raises_valueerror():
    with pytest.raises(ValueError):
        merge([(5, 1)])
    with pytest.raises(ValueError):
        merge([(1, 3), (10, 2), (4, 6)])
    # start == end must NOT raise — it is a valid (empty) interval.
    assert merge([(4, 4)]) == []


# ---------------------------------------------------------------------------
# Test 10: purity — merge must not mutate the input list or its tuples.
# ---------------------------------------------------------------------------
def test_does_not_mutate_input():
    arg = [(5, 7), (1, 3), (2, 6), (3, 3)]
    before = copy.deepcopy(arg)
    merge(arg)
    assert arg == before, "merge mutated its input list/elements"


# ---------------------------------------------------------------------------
# Test 11: output is a list of (int, int) tuples (record/shape contract).
# ---------------------------------------------------------------------------
def test_output_shape_int_tuples():
    out = merge([(1, 3), (3, 5), (8, 9)])
    assert isinstance(out, list)
    assert out == [(1, 5), (8, 9)]
    for iv in out:
        assert isinstance(iv, tuple) and len(iv) == 2
        assert isinstance(iv[0], int) and isinstance(iv[1], int)


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
