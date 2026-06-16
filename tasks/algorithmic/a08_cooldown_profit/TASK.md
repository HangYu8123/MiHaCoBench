# Algorithmic 08 — `max_profit`: weighted interval scheduling with a mandatory cooldown gap

**Created:** 2026-06-16 · **Category:** algorithmic · **Weight:** 8

Implement maximum-profit non-overlapping weighted interval scheduling, **twisted**
by a mandatory cooldown gap between consecutive chosen jobs, in a **single file**
`solution.py` using the **standard library only**.

## Public contract

```python
def max_profit(jobs: list[tuple], gap: int) -> int:
    """Select a subset of non-overlapping jobs, respecting a cooldown gap,
    that maximizes total profit. Return the maximum total profit."""
```

* Each job is a tuple `(start, end, profit)` with integer `start < end` and
  `profit >= 0`. Intervals are **half-open** `[start, end)`.
* A subset is **valid** when, ordering the chosen jobs by position, every chosen
  job's `start` is at least the previous chosen job's `end` **plus** `gap`
  (a required cooldown of at least `gap` between consecutive selected jobs).
  Equivalently, for any two chosen jobs the later one's `start >= the earlier
  one's end + gap`.
* `gap` is a non-negative integer. With `gap = 0` the rule reduces to ordinary
  non-overlapping scheduling on half-open intervals: two jobs with
  `prevEnd <= nextStart` may both be chosen.
* Return the **maximum total profit**, or `0` if `jobs` is empty.

### Boundary clarifications (read carefully)

* Two jobs are co-selectable iff `prevEnd + gap <= nextStart`. Separation of
  **exactly** `gap` is allowed; separation of `gap - 1` is **not**.
  Example: a job ending at `10` and a job starting at `13` are both selectable
  when `gap = 3` (since `10 + 3 == 13`), but **not** when `gap = 4`
  (since `10 + 4 = 14 > 13`).
* Profit may be `0`; a zero-profit job never reduces the optimum.
* The input list and its tuples must **not** be mutated.

## Complexity requirement (hard-gated in the grader)

| Requirement | Detail |
|---|---|
| **Time** | `O(n log n)` for `n` jobs. Sort by end, then DP with a binary search over earlier ends plus a running prefix maximum. A naive `O(n^2)` DP is correct but **times out** on the large input. |

### Concrete gate value (in the grader)

* **Time gate:** `N = 200000` jobs (fixed seed `random.Random(2026)`, starts in
  `[0, 5_000_000]`, durations in `[1, 50]`, profits in `[0, 1000]`, `gap = 7`)
  must complete within **6 seconds**. An `O(n^2)` DP (~4·10^10 operations)
  cannot finish in time.

## Why a greedy is wrong

A greedy that picks the highest-profit job first (or earliest-ending first
without DP) is **suboptimal**: a single high-profit job can block a *cluster* of
smaller jobs whose combined profit is larger. For example, with `gap = 0`:

```
jobs = [(0, 100, 10), (0,10,3), (10,20,3), (20,30,3), (30,40,3), (40,50,3)]
max_profit(jobs, 0) == 15   # the five abutting small jobs beat the one big job
```

A profit-descending greedy returns `10` here; the correct answer is `15`.

## Examples

```
max_profit([], 0)                                   == 0
max_profit([(0, 10, 7)], 0)                         == 7
max_profit([(0, 10, 5), (5, 15, 9)], 0)             == 9    # overlap -> better one
max_profit([(0, 10, 5), (13, 20, 6)], 3)            == 11   # gap exactly 3 -> both
max_profit([(0, 10, 5), (13, 20, 6)], 4)            == 6    # gap 4 -> only one
```

## Notes

* The result is a non-negative integer with no randomness.
* No length constraint beyond what is tested; the time gate above is the binding
  performance requirement.
