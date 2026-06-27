class TokenBucket:
    """Continuous (fractional) token-bucket rate limiter."""

    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if refill_rate < 0:
            raise ValueError("refill_rate must be >= 0")
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_now = None  # set on first allow() call (defines the epoch)

    def allow(self, now: float, cost: float = 1.0) -> bool:
        if cost <= 0:
            raise ValueError("cost must be > 0")

        if self.last_now is None:
            # First call: define the epoch, no refill.
            self.last_now = now
        else:
            if now < self.last_now:
                raise ValueError("now must be non-decreasing")
            elapsed = now - self.last_now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_now = now

        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
