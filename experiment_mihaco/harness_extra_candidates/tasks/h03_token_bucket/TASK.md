# Harness 03 — `TokenBucket`: Continuous Token-Bucket Rate Limiter

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 5

Implement a continuous (fractional) **token-bucket** rate limiter. A bucket holds
up to `capacity` tokens and refills *continuously* at `refill_rate` tokens per
unit of time. Each request is checked against the bucket at an absolute timestamp
`now` and either admitted (consuming tokens) or denied. The difficulty is entirely
in the **bookkeeping semantics** — exactly when the bucket refills, what counts as
"enough" tokens, and what state changes on a *denied* request. Misreading any one
of these admits or denies the wrong requests.

Implement your solution in a single file `solution.py` exposing the class below.
Use only the Python standard library (no third-party packages).

## Public contract

### class `TokenBucket`

#### `__init__(self, capacity: float, refill_rate: float)`

Create a bucket that holds **at most** `capacity` tokens and refills continuously
at `refill_rate` tokens per unit time. The bucket **starts full** (it holds
`capacity` tokens at creation).

| Condition | Raise |
|-----------|-------|
| `capacity <= 0` | `ValueError` |
| `refill_rate < 0` | `ValueError` |

#### `allow(self, now: float, cost: float = 1.0) -> bool`

Attempt to admit one request of size `cost` at absolute time `now`. Returns
`True` if the request is admitted, `False` if it is denied.

The semantics are exact:

1. **Refill happens on every call, before the decision.** Let
   `elapsed = now - last_now`, where `last_now` is the time of the *previous*
   call, or the bucket's creation time for the very first call. The **first**
   `allow`'s `now` defines the epoch and therefore produces **no** refill
   (`elapsed` is treated as 0). The new token level is
   `min(capacity, tokens + elapsed * refill_rate)`. This refill — **including
   advancing `last_now` to `now`** — is applied on **every** call, whether the
   request is ultimately allowed or denied.

2. **Admission is inclusive.** After refilling, the request is admitted **iff
   `tokens >= cost`** (a request whose `cost` exactly equals the currently
   available tokens **is** admitted). If admitted: subtract `cost` from `tokens`
   and return `True`. If denied: leave `tokens` unchanged and return `False`.

3. **Time is non-decreasing.** Passing `now < last_now` raises `ValueError`. A
   `now` **equal** to the previous call's time is allowed and produces zero
   refill (the same instant).

4. `cost <= 0` raises `ValueError`.

## Worked example

```python
b = TokenBucket(capacity=10, refill_rate=1)   # starts full at 10 tokens

b.allow(now=0,   cost=4)   # -> True   (10 >= 4; tokens -> 6; epoch t=0, no refill)
b.allow(now=0,   cost=6)   # -> True   (same instant, no refill; 6 >= 6 inclusive; tokens -> 0)
b.allow(now=0,   cost=1)   # -> False  (0 >= 1 is false; tokens stay 0; last_now still advances)
b.allow(now=3,   cost=3)   # -> True   (refill 3*1=3 -> tokens 3; 3 >= 3 inclusive; tokens -> 0)
b.allow(now=100, cost=10)  # -> True   (refill clamped to capacity 10, not 0+100; tokens -> 0)
```

## Notes

* The bucket is **stateful**: each `allow` reads and updates the bucket's token
  level and the time of the last call.
* All arithmetic is on real (fractional) values; `capacity`, `refill_rate`,
  `now`, and `cost` may be non-integers in general.
* Assert exception **types**; messages are unspecified.
* Determinism: the bucket's behaviour is fully determined by the sequence of
  `(now, cost)` calls; there is no randomness and no seed.
