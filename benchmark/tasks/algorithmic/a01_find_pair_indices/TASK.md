# Algorithmic 01 — `find_pair_indices`: two-sum with tiebreaking

**Created:** 2026-06-15 · **Category:** algorithmic · **Difficulty:** easy · **Weight:** 2

Implement a single-file solution using the **standard library only**. Write your
solution as `solution.py`.

## Problem

Given a list of integers `nums` and an integer `target`, find two distinct
indices `i` and `j` (with `i < j`) such that `nums[i] + nums[j] == target`.

### Tiebreaking rule

If multiple valid pairs exist, return the pair with the **smallest `j`**. Among
all pairs sharing that smallest `j`, return the one with the **smallest `i`**.

If no valid pair exists, return `None`.

## Public contract (must match exactly)

```python
def find_pair_indices(nums: list[int], target: int) -> tuple[int, int] | None:
    ...
```

* Returns a `tuple[int, int]` `(i, j)` with `i < j` on success, or `None`.
* Must run in **O(n) time** using a hash map (dict). An O(n²) nested-loop
  solution will be rejected by the large-input timing gate (see below).

## Complexity gate (stated for candidates)

The grader will call your function on an input of length **2,000,000** and
require it to complete within **5.0 seconds**. An O(n²) implementation cannot
pass this gate.

## Notes

* Indices are zero-based.
* `nums` may contain duplicate values; handle them correctly.
* An empty list or a single-element list must return `None`.
* Determinism: identical input ⇒ identical output.
