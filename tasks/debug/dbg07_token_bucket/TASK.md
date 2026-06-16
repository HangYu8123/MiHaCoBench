# Debug 07 — `TokenBucket`: a rate limiter that denies on the refill boundary

**Created:** 2026-06-16 · **Category:** debug · **Weight:** 2

You are given a **buggy** token-bucket rate limiter. Find and fix the defect,
then write your corrected solution as `solution.py` (**standard library only**).
Keep the public contract below exactly; do not rename the class or method, or
change their signatures or return types.

## Buggy implementation

```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)   # starts FULL
        self.last = 0.0

    def allow(self, now):
        # check the current (stale) token count and consume first ...
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            admitted = True
        else:
            admitted = False
        # ... then refill afterwards, so the freshly-added tokens are only
        # visible to the NEXT call.
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        return admitted
```

## Symptom (failing behavior)

A bucket of capacity 1 refilling 1 token/second starts full. The first request
is admitted (consuming the token); after waiting exactly one second the bucket
has refilled exactly one token, so the next request should be admitted too.
Instead the buggy code denies it, because it tests the token count *before*
applying the refill for that call:

```text
>>> b = TokenBucket(capacity=1, refill_rate=1)
>>> b.allow(0.0)
True
>>> b.allow(1.0)
False   # actual   (wrong)
True    # expected — exactly one token has refilled by t=1.0
```

The initial burst, the steady-state deny, and the refill-to-capacity cap are all
already correct — only requests that land *exactly* on a refill boundary are
wrongly denied.

## Public contract (must match exactly)

```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None: ...
    def allow(self, now: float) -> bool: ...
```

* `TokenBucket(capacity, refill_rate)` models a bucket that holds at most
  `capacity` tokens and refills `refill_rate` tokens **per second**. The bucket
  **starts full** (`capacity` tokens) at time `0`.
* `allow(now)` processes one request that arrives at absolute time `now`
  (seconds). `now` is **non-decreasing** across successive calls on the same
  bucket. Each call does, **in this order**:
  1. **Refill first.** Let `elapsed` be the time since the previous call (since
     time `0` for the first call). Add `elapsed * refill_rate` tokens, capped at
     `capacity`: `tokens = min(capacity, tokens + elapsed * refill_rate)`. Tokens
     therefore **never exceed `capacity`**, and refill credit accrues only for
     the elapsed real time (a partial second adds only its fractional share — no
     over-crediting).
  2. **Then admit.** If `tokens >= 1.0` (admission is **inclusive** at exactly
     `1.0`), consume exactly one token (`tokens -= 1.0`) and return `True`
     (request admitted); otherwise consume nothing and return `False`.
* A request that brings the bucket to **exactly** `1.0` token via the refill in
  step 1 **is admitted** (the `>= 1.0` comparison is inclusive).

## Notes

* Standard library only. Determinism: identical call sequence ⇒ identical
  outputs. No floating-point exactness is required of your arithmetic beyond what
  the formulas above imply; the grader compares admit/deny decisions and uses a
  tolerance for any token-timing checks.
