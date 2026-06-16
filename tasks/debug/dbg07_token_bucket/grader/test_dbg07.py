"""Grader for debug/dbg07_token_bucket. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken admits against the STALE (pre-refill) token count, so requests that
land on a refill boundary are wrongly denied (FAIL_TO_PASS), while immediate
burst / empty-deny / no-refill behaviour is unchanged (PASS_TO_PASS).

Only the boolean admit/deny decisions of ``allow`` are part of the contract.
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "debug", "dbg07_token_bucket"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
TokenBucket = gu.load_callable(SOL, "solution.py", "TokenBucket")


# ----------------------------- PASS_TO_PASS ----------------------------- #
def test_starts_full_burst():
    # Bucket starts full: capacity immediate admits, then a deny (no time elapses,
    # so refill order is irrelevant -> same in gold and broken).
    b = TokenBucket(4, 2.0)
    assert [b.allow(0.0) for _ in range(4)] == [True, True, True, True]
    assert b.allow(0.0) is False


def test_first_request_admitted():
    # The very first request on a full bucket is always admitted.
    assert TokenBucket(1, 1.0).allow(0.0) is True
    assert TokenBucket(5, 0.5).allow(0.0) is True


def test_empty_immediate_deny():
    b = TokenBucket(2, 1.0)
    assert b.allow(0.0) is True
    assert b.allow(0.0) is True
    assert b.allow(0.0) is False  # drained, no time elapsed


def test_zero_refill_never_refills():
    b = TokenBucket(3, 0.0)
    assert [b.allow(0.0) for _ in range(3)] == [True, True, True]
    assert b.allow(100.0) is False  # refill_rate 0 -> never refills


# ----------------------------- FAIL_TO_PASS ----------------------------- #
def test_refill_boundary_exact():
    # capacity=1, 1 token/sec: admit at t=0, then exactly one token has refilled
    # by t=1.0, so the next request must be admitted. The buggy (admit-before-
    # refill) version denies it.
    b = TokenBucket(1, 1.0)
    assert b.allow(0.0) is True
    assert b.allow(1.0) is True


def test_admit_after_wait():
    # Drain, then wait long enough to refill; the first post-wait request must be
    # admitted (gold refills THEN admits; the bug admits against the stale empty count).
    b = TokenBucket(3, 1.0)
    assert [b.allow(0.0) for _ in range(3)] == [True, True, True]
    assert b.allow(5.0) is True


def test_partial_refill_reaches_one_token():
    # capacity=1, 2 tokens/sec: after draining, half a second refills exactly one
    # token, so the request at t=0.5 must be admitted.
    b = TokenBucket(1, 2.0)
    assert b.allow(0.0) is True       # drains to 0
    assert b.allow(0.5) is True       # 0.5s * 2/s = 1 token refilled -> admit


def test_sustained_rate_admits_each_interval():
    # At one request per refill period the bucket should admit every request.
    b = TokenBucket(1, 1.0)
    decisions = [b.allow(float(t)) for t in range(6)]
    assert decisions == [True, True, True, True, True, True]


# ----------------------------- advisory ----------------------------- #
@pytest.mark.code_quality
def test_code_quality():
    print("code_quality:", gu.code_quality_report(SOL))
