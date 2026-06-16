"""Grader for debug/dbg01_retry_runner. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold (fixed) reference, FAILS on the broken
(still-buggy) reference. The FAIL_TO_PASS tests probe the terminal "failed"
transition the bug omits; the PASS_TO_PASS tests guard the behaviour the buggy
code already gets right (success paths and attempt counts).
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "debug", "dbg01_retry_runner"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
run_with_retries = gu.load_callable(SOL, "solution.py", "run_with_retries")


# ---- FAIL_TO_PASS: the planted bug (no terminal "failed" transition) -------- #
def test_exhausted_budget_is_failed():
    # all attempts fail, budget = max_retries + 1 = 3 → must end "failed"
    res = run_with_retries([False, False, False], max_retries=2)
    assert res["status"] == "failed"
    assert res["attempts"] == 3


def test_zero_retries_single_failure_is_failed():
    res = run_with_retries([False], max_retries=0)
    assert res["status"] == "failed"
    assert res["attempts"] == 1


def test_budget_cap_fails_before_a_later_success():
    # success exists at index 3, but budget = 2 attempts → never reached → failed
    res = run_with_retries([False, False, False, True], max_retries=1)
    assert res["status"] == "failed"
    assert res["attempts"] == 2


def test_outcomes_exhausted_before_budget_is_failed():
    # only 2 outcomes given though budget = max_retries + 1 = 4; none succeed → failed
    res = run_with_retries([False, False], max_retries=3)
    assert res["status"] == "failed"
    assert res["attempts"] == 2


# ---- PASS_TO_PASS: behaviour the buggy code already handles ------------------ #
def test_first_attempt_succeeds():
    res = run_with_retries([True, False, False], max_retries=2)
    assert res["status"] == "succeeded"
    assert res["attempts"] == 1


def test_succeeds_on_a_retry():
    res = run_with_retries([False, True], max_retries=2)
    assert res["status"] == "succeeded"
    assert res["attempts"] == 2


def test_succeeds_on_last_allowed_attempt():
    res = run_with_retries([False, False, True], max_retries=2)
    assert res["status"] == "succeeded"
    assert res["attempts"] == 3


def test_zero_retries_immediate_success():
    res = run_with_retries([True], max_retries=0)
    assert res["status"] == "succeeded"
    assert res["attempts"] == 1


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
