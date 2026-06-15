# Algorithmic 03 — `window_maxima`: sliding-window maximum in O(n)

**Created:** 2026-06-15 · **Category:** algorithmic · **Weight:** 8 · **Difficulty:** hard

Implement a sliding-window maximum function that runs in **O(n)** time using a
monotonic deque.  Write your solution as a single file `solution.py`.  You may
use only the Python **standard library** (`collections.deque`, etc.).

## Public contract (must match exactly)

```python
def window_maxima(nums: list[int], k: int) -> list[int]:
    ...
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `nums` | `list[int]` | Input list of integers |
| `k` | `int` | Window size (number of elements per window) |

### Return value

Return a `list[int]` of length `len(nums) - k + 1` containing the maximum value
in each contiguous window of size `k`, in left-to-right order.

### Edge cases and errors

| Condition | Behaviour |
|---|---|
| `k <= 0` | Raise `ValueError` |
| `k > len(nums)` | Return `[]` (empty list) |
| `k == 1` | Return a copy of `nums` |
| `k == len(nums)` | Return `[max(nums)]` |

### Example

```python
window_maxima([1, 3, -1, -3, 5, 3, 6, 7], k=3)
# -> [3, 3, 5, 5, 6, 7]
```

## Complexity requirement

Your implementation **must** be O(n) in both time and space (n = `len(nums)`).
The grader enforces this with a large-input hard gate:

* N = 1 000 000, k = 1 000, timeout = **5.0 seconds**

A naïve O(n·k) per-window scan cannot finish within that budget.

## Notes

* Elements may be negative, zero, or repeated.
* Determinism: identical input ⇒ identical output (no randomisation).
* Do **not** import third-party packages; stdlib only.
