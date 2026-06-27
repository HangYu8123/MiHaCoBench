"""Gold reference for harness/h03_token_bucket.

A continuous (fractional) token-bucket rate limiter.

A bucket holds at most ``capacity`` tokens and refills continuously at
``refill_rate`` tokens per unit time. It starts full. Each ``allow(now, cost)``
call:

  1. Refills the bucket based on the time elapsed since the previous call
     (``min(capacity, tokens + elapsed * refill_rate)``) and advances the
     internal clock to ``now`` — on EVERY call, allowed or denied. The first
     call defines the epoch and produces no refill.
  2. Admits the request iff ``tokens >= cost`` (inclusive); on admission it
     subtracts ``cost``, otherwise it leaves the level unchanged.

Time must be non-decreasing (``now < last_now`` -> ValueError); ``cost <= 0``
and an invalid ``capacity``/``refill_rate`` at construction also raise
ValueError.
"""
from __future__ import annotations


class TokenBucket:
    """Continuous token-bucket rate limiter (see module docstring / TASK.md)."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        """Create a full bucket of ``capacity`` tokens refilling at ``refill_rate``.

        Raises
        ------
        ValueError
            If ``capacity <= 0`` or ``refill_rate < 0``.
        """
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        if refill_rate < 0:
            raise ValueError(f"refill_rate must be >= 0, got {refill_rate}")
        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate)
        self._tokens = float(capacity)  # starts full
        self._last_now: float | None = None  # set by the first allow() call

    def allow(self, now: float, cost: float = 1.0) -> bool:
        """Attempt to admit a request of size ``cost`` at absolute time ``now``.

        Refills the bucket for the elapsed time and advances the clock on every
        call (allowed or denied). Returns ``True`` and consumes ``cost`` tokens
        iff ``tokens >= cost`` after refilling; otherwise returns ``False`` and
        leaves the level unchanged.

        Raises
        ------
        ValueError
            If ``cost <= 0`` or ``now`` is earlier than the previous call's time.
        """
        if cost <= 0:
            raise ValueError(f"cost must be > 0, got {cost}")

        if self._last_now is None:
            # First call defines the epoch: no refill, just anchor the clock.
            elapsed = 0.0
        else:
            if now < self._last_now:
                raise ValueError(
                    f"time must be non-decreasing: now={now} < last={self._last_now}"
                )
            elapsed = now - self._last_now

        # Refill (clamped to capacity) and advance the clock — unconditionally.
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
        self._last_now = float(now)

        # Inclusive admission.
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False
