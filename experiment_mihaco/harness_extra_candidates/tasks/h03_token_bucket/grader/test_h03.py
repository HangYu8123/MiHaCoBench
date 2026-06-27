"""Grader for harness/h03_token_bucket.

Tests the public contract only (see TASK.md): the ``TokenBucket`` class and its
``allow(now, cost)`` method. Validity invariant: PASSES on the gold reference,
FAILS on the broken reference.

The broken reference plants two defects in ``allow``:
  (a) it advances the clock / applies the refill ONLY on an admitted request, so
      tokens that should accrue during a denied window are lost, and
  (b) it uses a strict ``tokens > cost`` admission test instead of the inclusive
      ``tokens >= cost``.

The exact-boundary, deny-then-accrue, and full-worked-example tests catch these;
the simple always-admitted-burst and exception-path tests still pass on the
broken variant.

All timings/rates/costs are chosen as exact (integer-valued) floats so every
admission decision is exact — the public API returns ``bool``, so we assert the
boolean sequences directly rather than comparing internal floats.
"""
from __future__ import annotations

import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h03_token_bucket"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

TokenBucket = getattr(gu.load_module(SOL, "solution.py"), "TokenBucket")


# ---------------------------------------------------------------------------
# Independent reference oracle (lives in the grader; does NOT import the gold).
# A structurally simple, direct transcription of the spec used to cross-check
# the candidate's allow() boolean sequence on committed fixed call streams.
# ---------------------------------------------------------------------------
class _OracleBucket:
    """Spec-faithful reference token bucket, independent of the gold solution."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if refill_rate < 0:
            raise ValueError("refill_rate must be >= 0")
        self.capacity = float(capacity)
        self.rate = float(refill_rate)
        self.tokens = float(capacity)  # full
        self.last = None  # epoch set by first call

    def allow(self, now: float, cost: float = 1.0) -> bool:
        if cost <= 0:
            raise ValueError("cost must be > 0")
        if self.last is None:
            elapsed = 0.0
        else:
            if now < self.last:
                raise ValueError("time must be non-decreasing")
            elapsed = now - self.last
        # Refill and advance the clock unconditionally.
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last = float(now)
        # Inclusive admission.
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


def _run_sequence(bucket, calls):
    """Drive ``bucket.allow`` over ``calls`` = list of (now, cost); return the
    list of returned booleans."""
    return [bucket.allow(now, cost) for (now, cost) in calls]


# The full worked-example call stream from TASK.md and its expected verdicts.
_WORKED_CALLS = [(0, 4), (0, 6), (0, 1), (3, 3), (100, 10)]
_WORKED_EXPECTED = [True, True, False, True, True]


# ---------------------------------------------------------------------------
# Test 1 [FAIL_TO_PASS]: the full worked-example sequence from TASK.md.
# Exercises exact-boundary inclusive admits, deny-does-not-stop-accrual, and the
# capacity clamp in one committed stream. The strict-"<" defect flips call 2
# (6>=6 admitted vs 6>6 denied); the "advance-only-on-allow" defect corrupts the
# accrual after the denied call 3.
# ---------------------------------------------------------------------------
def test_worked_example_sequence():
    b = TokenBucket(capacity=10, refill_rate=1)
    assert _run_sequence(b, _WORKED_CALLS) == _WORKED_EXPECTED


# ---------------------------------------------------------------------------
# Test 2 [FAIL_TO_PASS]: exact-boundary inclusive admit as its own focused case.
# A request whose cost EXACTLY equals the available tokens must be admitted.
# Directly kills the strict ``tokens > cost`` defect.
# ---------------------------------------------------------------------------
def test_exact_boundary_inclusive_admit():
    b = TokenBucket(capacity=5, refill_rate=0)  # no refill: level pinned at 5
    # cost == available tokens (5 == 5) must be ADMITTED.
    assert b.allow(now=0, cost=5) is True
    # Now empty; an exact zero-cost match is impossible (cost>0), so a 1-token
    # request is denied.
    assert b.allow(now=0, cost=1) is False


# ---------------------------------------------------------------------------
# Test 3 [FAIL_TO_PASS]: deny-then-accrue. After the bucket is drained to 0, a
# too-big request is denied at t=2; by t=5 enough has refilled to admit. A
# correct bucket admits the final request (5 tokens accrued, 5 >= 5 inclusive);
# the broken bucket diverges on this stream.
# ---------------------------------------------------------------------------
def test_deny_then_accrue():
    b = TokenBucket(capacity=10, refill_rate=1)
    # Drain to exactly 0 at t=0.
    assert b.allow(now=0, cost=10) is True          # tokens -> 0, last_now=0
    # At t=2: only 2 tokens have accrued (2*1), a cost-5 request is DENIED.
    assert b.allow(now=2, cost=5) is False          # refill -> 2, last_now=2 (denied)
    # At t=5: 5 tokens total have accrued from the epoch; the denied call must not
    # have stopped the accrual. 5 >= 5 (inclusive) -> ADMITTED.
    assert b.allow(now=5, cost=5) is True


# ---------------------------------------------------------------------------
# Test 4 [FAIL_TO_PASS]: a denied call must still refill and advance the clock,
# so a later request is decided from the bucket's state *as of the denied call*.
# Here both gold and broken DENY the middle request (it is not a boundary flip),
# but they diverge on the third: the gold bucket banked tokens at the denied
# call and tops out at capacity by t=5, admitting; the broken bucket — which
# neither refilled nor advanced its clock on the denied call — denies.
# ---------------------------------------------------------------------------
def test_denied_call_still_refills_and_advances():
    b = TokenBucket(capacity=8, refill_rate=1)
    assert b.allow(now=0, cost=3) is True    # tokens 8 -> 5, last_now -> 0
    # Middle request is too big for the current level; DENIED, but the bucket
    # must still refill (5 -> 6) and advance last_now to 1.
    assert b.allow(now=1, cost=8) is False
    # By t=5 the level has accrued from the denied call's time and clamped to
    # capacity (8); an 8-token request is admitted (inclusive).
    assert b.allow(now=5, cost=8) is True


# ---------------------------------------------------------------------------
# Test 5: capacity clamp after a long idle period. Tokens never exceed capacity
# no matter how long the bucket sits idle.
# ---------------------------------------------------------------------------
def test_capacity_clamp_after_long_idle():
    b = TokenBucket(capacity=8, refill_rate=3)
    assert b.allow(now=0, cost=8) is True            # drain to 0
    # After a very long idle the level is clamped to capacity (8), NOT 0+1000*3.
    assert b.allow(now=1000, cost=8) is True         # refill clamped to 8 -> admit
    assert b.allow(now=1000, cost=1) is False        # now empty (same instant)
    # A 9-token request can never be admitted (exceeds capacity even when full).
    b2 = TokenBucket(capacity=8, refill_rate=3)
    assert b2.allow(now=0, cost=9) is False


# ---------------------------------------------------------------------------
# Test 6: equal-`now` produces zero refill (the same instant). Two calls at the
# same timestamp see the same clock; no tokens accrue between them.
# ---------------------------------------------------------------------------
def test_equal_now_no_refill():
    b = TokenBucket(capacity=10, refill_rate=5)
    assert b.allow(now=7, cost=6) is True            # epoch t=7, tokens 10->4
    # Same instant: zero refill, so only 4 tokens remain; cost 5 is denied.
    assert b.allow(now=7, cost=5) is False
    # Still the same instant: cost 4 is exactly the level -> admitted (inclusive).
    assert b.allow(now=7, cost=4) is True


# ---------------------------------------------------------------------------
# Test 7: a simple always-admitted burst (HAPPY PATH — passes on BOTH variants).
# Every cost is strictly below the available level and every call advances time,
# so neither planted defect is triggered. Guards against over-fitting the grader.
# ---------------------------------------------------------------------------
def test_simple_admitted_burst_happy_path():
    b = TokenBucket(capacity=100, refill_rate=1)
    # Costs of 1 with capacity 100 are always strictly below the level.
    verdicts = [b.allow(now=t, cost=1) for t in range(10)]
    assert verdicts == [True] * 10


# ---------------------------------------------------------------------------
# Test 8: first call defines the epoch and produces NO refill. Even with a huge
# `now`, the first call sees exactly the starting (full) level.
# ---------------------------------------------------------------------------
def test_first_call_is_epoch_no_refill():
    b = TokenBucket(capacity=10, refill_rate=1000)
    # First call at a large now: no refill yet -> at most the full capacity (10).
    assert b.allow(now=10_000, cost=10) is True      # exactly full -> admit
    assert b.allow(now=10_000, cost=1) is False      # same instant, now empty


# ---------------------------------------------------------------------------
# Test 9: time must be non-decreasing -> ValueError when now < last_now.
# ---------------------------------------------------------------------------
def test_decreasing_time_raises_valueerror():
    b = TokenBucket(capacity=10, refill_rate=1)
    assert b.allow(now=5, cost=1) is True
    with pytest.raises(ValueError):
        b.allow(now=4, cost=1)
    # Equal time is fine (already covered) — a strictly earlier time is the error.
    with pytest.raises(ValueError):
        b.allow(now=0, cost=1)


# ---------------------------------------------------------------------------
# Test 10: cost <= 0 -> ValueError.
# ---------------------------------------------------------------------------
def test_nonpositive_cost_raises_valueerror():
    b = TokenBucket(capacity=10, refill_rate=1)
    with pytest.raises(ValueError):
        b.allow(now=0, cost=0)
    with pytest.raises(ValueError):
        b.allow(now=0, cost=-2)


# ---------------------------------------------------------------------------
# Test 11: invalid construction -> ValueError (capacity<=0, refill_rate<0).
# ---------------------------------------------------------------------------
def test_invalid_construction_raises_valueerror():
    with pytest.raises(ValueError):
        TokenBucket(capacity=0, refill_rate=1)
    with pytest.raises(ValueError):
        TokenBucket(capacity=-5, refill_rate=1)
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate=-1)
    # capacity > 0 and refill_rate == 0 is VALID (a non-refilling bucket): it
    # constructs and admits a request below its (full) starting level.
    b = TokenBucket(capacity=3, refill_rate=0)
    assert b.allow(now=0, cost=2) is True


# ---------------------------------------------------------------------------
# Test 12 [FAIL_TO_PASS]: independent-oracle agreement on committed, fixed
# random call streams. The candidate's allow() boolean sequence must match the
# spec-faithful _OracleBucket on every stream. now is non-decreasing within each
# stream; all values are integer-valued so decisions are exact.
# ---------------------------------------------------------------------------
def _make_streams():
    """Build several DETERMINISTIC (committed seeds) call streams of (now, cost)
    with non-decreasing `now`. Returned as (capacity, rate, calls) tuples."""
    streams = []
    configs = [
        # (capacity, rate, seed, n_calls, max_step, max_cost)
        (10, 1, 12345, 40, 3, 6),
        (5, 2, 6789, 50, 2, 4),
        (20, 1, 24680, 60, 4, 12),
        (8, 3, 13579, 45, 1, 9),
        (3, 0, 11111, 30, 5, 3),   # non-refilling bucket
    ]
    for capacity, rate, seed, n_calls, max_step, max_cost in configs:
        rng = random.Random(seed)
        now = 0
        calls = []
        for _ in range(n_calls):
            now += rng.randint(0, max_step)       # non-decreasing (can repeat)
            cost = rng.randint(1, max_cost)       # cost >= 1 (valid)
            calls.append((now, cost))
        streams.append((capacity, rate, calls))
    return streams


@pytest.mark.parametrize("capacity,rate,calls", _make_streams())
def test_matches_independent_oracle(capacity, rate, calls):
    candidate = TokenBucket(capacity=capacity, refill_rate=rate)
    oracle = _OracleBucket(capacity=capacity, refill_rate=rate)
    got = _run_sequence(candidate, calls)
    expected = _run_sequence(oracle, calls)
    assert got == expected, (
        f"verdict mismatch for capacity={capacity}, rate={rate}\n"
        f"first divergence at index "
        f"{next((i for i, (a, b) in enumerate(zip(got, expected)) if a != b), None)}"
    )


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail).
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
