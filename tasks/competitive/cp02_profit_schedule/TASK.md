# Competitive 02 — `max_profit`: Weighted Interval Scheduling

**Created:** 2026-06-15 · **Category:** competitive · **Weight:** 8

Implement the classic **Weighted Interval Scheduling** problem in a **single file** `solution.py`
using the **standard library only** (no numpy, no external packages).

## Problem statement

You are given a list of jobs. Each job is a tuple `(start, end, profit)` where:

- `start` — the integer time the job begins (inclusive)
- `end` — the integer time the job finishes (exclusive)
- `profit` — the integer profit gained by selecting this job (may be negative)

Two jobs **conflict** if their intervals overlap. Specifically, a job ending at time `t`
**conflicts** with a job starting at time `t` — i.e., `next.start < prev.end` means conflict,
and `next.start >= prev.end` means they are **compatible** (can both be selected).

Select a subset of **non-overlapping** (mutually compatible) jobs to **maximise total profit**.
You may select zero jobs. Jobs with negative profits should never be selected.

## Public contract

```python
def max_profit(jobs: list[tuple[int, int, int]]) -> int:
    """Return the maximum total profit from a non-overlapping subset of jobs.

    Parameters
    ----------
    jobs : list of (start, end, profit) tuples
        Each entry is (start: int, end: int, profit: int).
        Jobs where end <= start are invalid and will not appear in test inputs.
        Profits may be negative (such jobs should simply not be selected).

    Returns
    -------
    int
        Maximum achievable total profit. Returns 0 if no profitable selection exists
        (e.g., all profits are negative, or jobs is empty).

    Complexity
    ----------
    Expected: O(n log n) using DP + binary search (sort by end time, bisect for
    the latest compatible predecessor).
    """
```

## Complexity requirements (hard-gated in the grader)

| Requirement | Detail |
|---|---|
| **Time** | O(n log n) — sort by end + DP with binary search for latest compatible predecessor |
| **Hard gate** | n = 100 000 jobs (fixed seed) — must complete within **5 seconds** |

An O(n²) solution using a nested loop for the predecessor search will time out on n = 100 000.

## Adjacency / boundary rule

If job A ends at time `t` and job B starts at time `t`, they are **compatible** (not conflicting).
The condition for compatibility is: `job_B.start >= job_A.end`.

## Examples

```
max_profit([])                                  == 0   # no jobs
max_profit([(1, 3, 50)])                        == 50  # single job
max_profit([(1, 4, 30), (3, 6, 60)])            == 60  # overlapping: pick better
max_profit([(1, 3, 30), (3, 5, 40)])            == 70  # adjacent: pick both
max_profit([(1, 5, -10)])                       == 0   # negative profit: skip
max_profit([(1, 3, 10), (2, 5, 15), (4, 6, 8)]) == 23 # pick (1,3,10) + (4,6,8)=18? No, (2,5,15)+(... only?) best is (2,5,15)+(nothing if disjoint)
```

More carefully:
```
jobs = [(1, 3, 10), (2, 5, 15), (4, 6, 8)]
# Compatible pairs: (1,3,10) and (4,6,8) → profit 18
# Or just (2,5,15) → profit 15
# Best: (1,3,10) + (4,6,8) = 18
max_profit(jobs) == 18
```

## Notes

- Return `0` if `jobs` is empty or if every job has non-positive profit.
- The result is always a non-negative integer.
- Duplicate jobs (identical tuples) may appear; treat each occurrence independently.
- Input `jobs` may be given in any order.
