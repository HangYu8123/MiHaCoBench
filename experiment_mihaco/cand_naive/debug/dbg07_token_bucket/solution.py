class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)  # starts FULL
        self.last = 0.0

    def allow(self, now: float) -> bool:
        # Step 1: Refill first.
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        # Step 2: Then admit.
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        else:
            return False
