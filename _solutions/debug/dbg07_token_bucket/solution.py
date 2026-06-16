"""Gold reference for debug/dbg07_token_bucket — a token-bucket rate limiter.

The original code admitted a request *before* applying the refill for that call,
so the freshly-accrued tokens were only visible to the *next* request. A request
that arrived exactly when the bucket had refilled its first token was therefore
wrongly denied (an off-by-one in the refill/admit ordering, compounded by the
inclusive ``>= 1.0`` admission threshold).

The fix follows the contract's order: **refill first** (capping at ``capacity``),
**then admit** when ``tokens >= 1.0`` (inclusive), consuming exactly one token.
"""
from __future__ import annotations


class TokenBucket:
    """A token bucket holding up to ``capacity`` tokens, refilling ``refill_rate``
    tokens per second and starting full at time ``0``.

    ``allow(now)`` refills for the time elapsed since the previous call (capped at
    ``capacity``), then admits the request iff at least one token is available.
    """

    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)  # the bucket starts full
        self.last = 0.0

    def allow(self, now: float) -> bool:
        """Refill based on elapsed time, then admit one request if a token is free.

        ``now`` is non-decreasing across calls. Refill happens *first* (so a token
        that accrues exactly at ``now`` counts toward this request) and is capped
        at ``capacity``; admission is inclusive at ``tokens == 1.0``.
        """
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False
