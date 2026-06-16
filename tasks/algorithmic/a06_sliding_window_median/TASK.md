# Algorithmic 06 — `sliding_window_median`: sliding-window median in O(n log k)

**Created:** 2026-06-15 · **Category:** algorithmic · **Weight:** 8 · **Difficulty:** hard

Implement a sliding-window median function that runs in **O(n log k)** time using
two heaps with lazy deletion.  Write your solution as a single file `solution.py`.
You may use only the Python **standard library** (`heapq`, `collections`, etc.).

## Public contract (must match exactly)

```python
def sliding_window_median(nums: list[float], k: int) -> list[float]:
    ...
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `nums` | `list[float]` | Input list of numbers (may be int or float) |
| `k` | `int` | Window size (number of elements per window) |

### Return value

Return a `list[float]` of length `len(nums) - k + 1` containing the median of
each contiguous window of size `k`, in left-to-right order.

* **Odd k**: the median is the middle element when the window is sorted.
* **Even k**: the median is the **average of the two middle values** (i.e.
  `(sorted_window[k//2 - 1] + sorted_window[k//2]) / 2`).

### Edge cases and errors

| Condition | Behaviour |
|---|---|
| `k <= 0` | Raise `ValueError` |
| `k > len(nums)` | Return `[]` (empty list) |
| `k == 1` | Return each element as a float (copy of `nums` as `list[float]`) |
| `k == len(nums)` | Return a single-element list with the overall median |

### Example

```python
sliding_window_median([1, 3, -1, -3, 5, 3, 6, 7], k=3)
# -> [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]

sliding_window_median([1, 2, 3, 4], k=2)
# -> [1.5, 2.5, 3.5]
```

## Complexity requirement

Your implementation **must** be O(n log k) in time (n = `len(nums)`, k = window size).
The grader enforces this with a large-input hard gate:

* N = 200 000, k = 1 000, timeout = **8.0 seconds**

A naïve O(n·k) re-sort-each-window approach cannot finish within that budget.

## Notes

* Elements may be negative, zero, repeated, or floating-point.
* Determinism: identical input ⇒ identical output.
* Do **not** import third-party packages; stdlib only.
