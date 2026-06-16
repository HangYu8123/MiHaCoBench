"""Deliberately-broken reference for debug/dbg07_token_bucket.

Planted defect (a c01-style boundary off-by-one in *ordering*): ``allow`` tests
and consumes the **stale** token count *before* applying this call's refill, so
the tokens that accrue for the elapsed interval are only visible to the *next*
request. A request that arrives exactly when the bucket has refilled its first
token is therefore wrongly denied — it sees the pre-refill (empty) bucket.

The defect is localized: the initial burst, the steady-state deny, the
refill-to-capacity cap, and partial-second (no over-credit) refills all still
behave correctly, because for those cases the refill-vs-admit order does not
change the decision. Only requests landing *on* a refill boundary differ. The
grader must catch this ordering bug (FAIL_TO_PASS) while every PASS_TO_PASS test
still holds.
"""
from __future__ import annotations


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)  # the bucket starts full
        self.last = 0.0

    def allow(self, now: float) -> bool:
        # BUG: admit against the stale token count BEFORE refilling, so tokens
        # that accrue for this interval only count toward the next request.
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            admitted = True
        else:
            admitted = False
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        return admitted
