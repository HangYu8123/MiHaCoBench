# Algorithmic 02 — `longest_distinct_window`: length of the longest subarray with all-distinct elements

**Created:** 2026-06-15 · **Category:** algorithmic · **Difficulty:** medium · **Weight:** 4

Implement a single-file solution using the **standard library only**. Write your
solution as `solution.py`.

## Problem

Given a list of integers `seq`, return the **length** of the longest contiguous
subarray (window) in which every element is distinct (no duplicates within the
window).

### Examples

| `seq`                        | result |
|------------------------------|--------|
| `[]`                         | `0`    |
| `[5]`                        | `1`    |
| `[1, 2, 3, 4]`               | `4`    |
| `[1, 1, 1, 1]`               | `1`    |
| `[1, 2, 3, 1, 2, 3, 4, 5]`  | `5`    |
| `[1, 2, 1, 3, 2, 4]`        | `4`    |

## Public contract (must match exactly)

```python
def longest_distinct_window(seq: list[int]) -> int:
    ...
```

* `seq` — a list of integers (may be empty).
* Returns a non-negative integer — the length of the longest contiguous
  subarray with all distinct elements. Returns `0` for an empty list.
* Must run in **O(n) time** using a sliding-window approach with a last-seen
  map (dict). An O(n²) implementation will be rejected by the large-input
  timing gate (see below).

## Complexity gate (stated for candidates)

The grader will call your function on an input of length **1,000,000** and
require it to complete within **5.0 seconds**. An O(n²) implementation cannot
pass this gate.

## Notes

* Elements are plain Python `int` values.
* An empty list must return `0`.
* A single-element list must return `1`.
* All elements identical → returns `1`.
* All elements distinct → returns `len(seq)`.
* Determinism: identical input ⇒ identical output.
