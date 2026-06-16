"""Grader for debug/dbg04_paginate. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold (fixed) reference, FAILS on the broken
(still-buggy) reference. FAIL_TO_PASS tests pin the exact slice content per page
(the off-by-one shifts it); PASS_TO_PASS tests guard argument validation and the
out-of-range / empty cases the buggy code already gets right.
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "debug", "dbg04_paginate"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
paginate = gu.load_callable(SOL, "solution.py", "paginate")

DATA = [10, 20, 30, 40, 50]


# ---- FAIL_TO_PASS: the 1-indexed boundary the bug shifts -------------------- #
def test_first_page():
    assert paginate(DATA, page=1, page_size=2) == [10, 20]


def test_second_page():
    assert paginate(DATA, page=2, page_size=2) == [30, 40]


def test_last_partial_page():
    assert paginate(DATA, page=3, page_size=2) == [50]


def test_page_size_one_indexing():
    assert paginate(DATA, page=1, page_size=1) == [10]
    assert paginate(DATA, page=5, page_size=1) == [50]


# ---- PASS_TO_PASS: validation / out-of-range the buggy code already handles -- #
def test_page_beyond_data_is_empty():
    assert paginate(DATA, page=100, page_size=2) == []


def test_empty_records_is_empty():
    assert paginate([], page=1, page_size=3) == []


def test_invalid_page_raises():
    with pytest.raises(ValueError):
        paginate(DATA, page=0, page_size=2)


def test_invalid_page_size_raises():
    with pytest.raises(ValueError):
        paginate(DATA, page=1, page_size=0)


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
