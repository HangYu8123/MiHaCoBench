# Algorithmic 09 — `interval_stab`: minimum points to stab all closed intervals

**Created:** 2026-06-16 · **Category:** algorithmic · **Weight:** 4

Implement a **single file** `solution.py` (standard library only).

## Public contract (must match exactly)

```python
def min_stabbing_points(intervals: list[tuple]) -> int:
    """Return the minimum number of points on the real line such that every
    interval contains at least one chosen point.

    Each interval is a tuple ``(a, b)`` with ``a <= b`` and represents the
    **closed** interval ``[a, b]``. A point ``p`` **stabs** ``[a, b]`` iff
    ``a <= p <= b`` (inclusive at BOTH ends).

    An empty list returns ``0``.
    """
```

## Semantics (read carefully)

* Intervals are **closed**: `[a, b]` includes both endpoints.
* Because the endpoints are included, two intervals that merely **touch** at an
  endpoint share that point. For example `[1, 2]` and `[2, 3]` are both stabbed
  by the single point `2`, so the answer for `[[1, 2], [2, 3]]` is **1** (not 2).
* Inputs may be given in any order.

## Examples

```python
min_stabbing_points([])                        == 0
min_stabbing_points([(5, 7)])                  == 1
min_stabbing_points([(1, 10), (3, 4)])         == 1   # point 4 stabs both
min_stabbing_points([(1, 2), (5, 6), (9, 10)]) == 3   # pairwise disjoint
min_stabbing_points([(1, 2), (2, 3)])          == 1   # touch at 2 → one point
min_stabbing_points([(0, 1), (1, 2), (2, 3), (3, 4)]) == 2   # points 1 and 3
```

## Constraints

* `0 <= len(intervals)`; integer or float endpoints with `a <= b`.
* Aim for `O(n log n)` (sort by right endpoint, greedy). Return a plain `int`.
