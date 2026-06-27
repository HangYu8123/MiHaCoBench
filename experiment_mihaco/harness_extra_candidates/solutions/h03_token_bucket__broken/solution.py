"""BROKEN reference for harness/h03_token_bucket.

PLANTED DEFECTS (localized to ``allow``):

  (a) The refill / clock advance is applied ONLY when the request is admitted.
      A denied request leaves ``last_now`` (and the token level) unchanged, so
      the time it consumed is "lost": tokens that should have accrued during a
      denied window are never credited. (Gold advances the clock on EVERY call.)

  (b) Admission uses a STRICT ``tokens > cost`` test instead of the inclusive
      ``tokens >= cost``. A request whose cost exactly equals the available
      tokens is wrongly denied.

Capacity clamping is kept correct. These defects pass simple always-admitted
bursts (where every call advances the clock anyway and costs are strictly below
the level) but fail the exact-boundary admits and the deny-then-later-allow
accrual.
"""
from __future__ import annotations


class TokenBucket:
    """Continuous token-bucket rate limiter (see TASK.md)."""

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
        self._last_now: float | None = None

    def allow(self, now: float, cost: float = 1.0) -> bool:
        """Attempt to admit a request of size ``cost`` at absolute time ``now``.

        Raises
        ------
        ValueError
            If ``cost <= 0`` or ``now`` is earlier than the previous call's time.
        """
        if cost <= 0:
            raise ValueError(f"cost must be > 0, got {cost}")

        if self._last_now is None:
            elapsed = 0.0
        else:
            if now < self._last_now:
                raise ValueError(
                    f"time must be non-decreasing: now={now} < last={self._last_now}"
                )
            elapsed = now - self._last_now

        # Compute the would-be refilled level (clamped) without committing it yet.
        refilled = min(self._capacity, self._tokens + elapsed * self._refill_rate)

        # BUG (b): strict ">" instead of inclusive ">=".
        if refilled > cost:
            # BUG (a): only on admission do we commit the refill and advance the
            # clock. A denied call therefore neither refills nor advances time.
            self._tokens = refilled - cost
            self._last_now = float(now)
            return True
        return False
