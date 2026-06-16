# Debug 06 — `interval_merge`: merging overlapping intervals

**Created:** 2026-06-15 · **Category:** debug · **Weight:** 2

You are given a **buggy** implementation of an interval-merging function.
Find and fix the defect, then write your corrected solution as `solution.py`
(**standard library only**). Keep the public contract below exactly; do not
rename the function or change its return shape.

## Buggy implementation

```python
def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    result = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = result[-1]
        if start < last_end:          # BUG: should be <= to handle touching intervals
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
```

## Symptom (failing behaviour)

Intervals that **touch** at a shared endpoint should be merged into one.
Instead the function leaves them separate:

```text
>>> merge_intervals([(1, 3), (3, 5)])
[(1, 3), (3, 5)]   # actual   (wrong)
[(1, 5)]           # expected
```

Clearly overlapping intervals and empty/single-interval inputs are already
handled correctly.

## Public contract (must match exactly)

```python
def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    ...
```

* Each element of `intervals` is a `(start, end)` tuple of integers with
  `start <= end`.
* The function must **sort** the intervals by start endpoint before merging
  (do not assume the input is pre-sorted).
* Two intervals `(a, b)` and `(c, d)` are merged whenever `c <= b` — i.e.
  they overlap **or** share an endpoint ("touching" intervals).
* Return a list of non-overlapping, non-touching intervals sorted by start
  endpoint, as `(start, end)` tuples.

## Notes

* Standard library only. Determinism: identical input ⇒ identical output.
* A **chain** of touching intervals (e.g. `(0,1),(1,2),(2,3)`) must collapse
  to a single interval `(0,3)`.
