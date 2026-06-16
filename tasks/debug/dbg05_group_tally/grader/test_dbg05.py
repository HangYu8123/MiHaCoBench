"""Grader for debug/dbg05_group_tally. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold (fixed) reference, FAILS on the broken
(still-buggy) reference. The FAIL_TO_PASS tests deliberately make *multiple
no-argument calls within a single test* — the mutable-default bug only surfaces
when the shared default object persists across calls — and assert each call
starts fresh. The PASS_TO_PASS tests always pass an explicit ``groups`` dict (the
path the bug does not touch), guarding in-place accumulation.
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "debug", "dbg05_group_tally"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
tally_by_group = gu.load_callable(SOL, "solution.py", "tally_by_group")


# ---- FAIL_TO_PASS: no-arg calls must not share state ------------------------ #
def test_independent_no_arg_calls_are_fresh():
    first = tally_by_group("alpha", 1)
    second = tally_by_group("beta", 2)
    assert second == {"beta": [2]}      # must not contain "alpha" from the first call
    assert first == {"alpha": [1]}
    assert first is not second          # each no-arg call gets its own dict


def test_repeated_no_arg_call_does_not_accumulate():
    r1 = tally_by_group("k", "a")
    r2 = tally_by_group("k", "b")
    assert r1 == {"k": ["a"]}
    assert r2 == {"k": ["b"]}


# ---- PASS_TO_PASS: explicit-dict accumulation the buggy code already handles - #
def test_explicit_dict_accumulates():
    acc = {}
    tally_by_group("x", 1, acc)
    tally_by_group("x", 2, acc)
    tally_by_group("y", 3, acc)
    assert acc == {"x": [1, 2], "y": [3]}


def test_returns_the_passed_object():
    acc = {}
    out = tally_by_group("x", 1, acc)
    assert out is acc


def test_multiple_labels_with_explicit_dict():
    acc = {}
    for label, value in [("a", 1), ("b", 2), ("a", 3)]:
        tally_by_group(label, value, acc)
    assert acc == {"a": [1, 3], "b": [2]}


def test_value_can_be_any_type():
    acc = tally_by_group("nums", 1, {})
    tally_by_group("nums", [2, 3], acc)
    assert acc == {"nums": [1, [2, 3]]}


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
