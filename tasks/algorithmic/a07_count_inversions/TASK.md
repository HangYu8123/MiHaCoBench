# Algorithmic 07 — `count_inversions`: inversion count via merge-sort or BIT

**Created:** 2026-06-15 · **Category:** algorithmic · **Weight:** 8

Implement the classic **inversion counter** in a **single file** `solution.py`
using the **standard library only**.

## Public contract

```python
def count_inversions(nums: list[int]) -> int:
    """Return the number of inversion pairs (i, j) with i < j and nums[i] > nums[j].

    Equal elements are NOT considered an inversion.
    """
```

### Constraints

* `nums` is a list of integers (may be negative, zero, or large).
* Duplicate values: equal elements with i < j do NOT count as an inversion.
* The empty list and a single-element list each have **0** inversions.
* Sorted ascending → **0** inversions.
* Sorted descending (all distinct) of length *n* → **n*(n-1)/2** inversions.

## Complexity requirements (hard-gated in the grader)

| Requirement | Detail |
|---|---|
| **Time** | O(n log n) — merge-sort counting or a Fenwick/BIT over compressed values. |

### Concrete gate values (in the grader)

* **Hard time gate:** array of length **200 000** — must complete within **5 seconds**.
  A naïve O(n²) double loop requires ~40 billion comparisons at n=200 000 and
  will time out; an O(n log n) solution completes in well under 1 second.

## Examples

```
count_inversions([])            == 0
count_inversions([1])           == 0
count_inversions([1, 2, 3])     == 0      # sorted ascending
count_inversions([3, 2, 1])     == 3      # n*(n-1)/2 = 3
count_inversions([2, 4, 1, 3])  == 3      # (2,1), (4,1), (4,3)
count_inversions([1, 1, 1])     == 0      # duplicates, no inversions
count_inversions([3, 1, 2])     == 2      # (3,1) and (3,2)
count_inversions([-3, -1, -2])  == 1      # (-1,-2): one inversion among negatives
```

## Notes

* Return type must be **int**.
* The function is pure: it must not mutate `nums`.
* Determinism: the result is an integer with no randomness.
