# Competitive 05 — `kth_subarray_sum`: k-th Smallest Contiguous-Subarray Sum

**Created:** 2026-06-16 · **Category:** competitive · **Weight:** 8

Implement a **single file** `solution.py` (standard library only) that, given a
non-negative integer array, returns the **k-th smallest** sum among **all**
contiguous-subarray sums.

## Public contract

```python
def kth_subarray_sum(a: list[int], k: int) -> int:
    """Return the k-th SMALLEST contiguous-subarray sum (1-indexed) of `a`.

    Parameters
    ----------
    a : list[int]
        A list of n >= 1 NON-NEGATIVE integers (values may be 0).
    k : int
        A 1-indexed rank, with 1 <= k <= n*(n+1)/2.

    Returns
    -------
    int
        The k-th smallest value among ALL n*(n+1)/2 contiguous-subarray sums.
        A contiguous subarray is a[i..j] for 0 <= i <= j <= n-1 (its sum is
        a[i] + a[i+1] + ... + a[j]). There are exactly n*(n+1)/2 such subarrays
        (single elements included). Collect every one of their sums; the answer
        is the k-th smallest of that multiset (duplicate sums each count, so two
        different subarrays with equal sums occupy two consecutive ranks).
    """
```

### Definition details (read carefully)

* The multiset has exactly `n*(n+1)/2` elements — one per contiguous subarray,
  **counting single-element subarrays** `a[i..i]`. Equal sums are **not**
  deduplicated: if three subarrays share a sum value, they fill three consecutive
  ranks.
* `k` is **1-indexed**: `k = 1` selects the smallest sum, `k = n*(n+1)/2` selects
  the largest sum (the sum of the whole array). Because all elements are
  non-negative, the smallest sum equals `min(a)` and the largest equals `sum(a)`.
* Values may be `0`. The array always has at least one element (`n >= 1`); for
  `n == 1` the only subarray is `a[0]` and `k` must be `1`, so return `a[0]`.

## Algorithm requirement (hard-gated)

| Requirement | Detail |
|---|---|
| **Time** | `O(n log(totalSum))`. Binary-search the answer `S` over `[min(a), sum(a)]`; for each candidate `S`, count subarrays with sum `<= S` using a **two-pointer sliding window** (valid because all elements are non-negative, so window sums are monotonic); return the smallest `S` whose count is `>= k`. |
| **Forbidden at scale** | Enumerating all `n*(n+1)/2` subarray sums (the O(n^2) "enumerate-and-sort") is correct but blows the gate below. |

The count of subarrays with sum `<= S` is a non-decreasing step function of `S`,
so the smallest `S` with `count(<= S) >= k` is exactly the k-th smallest sum.

### Concrete gate values (enforced by the grader)

* **Hard time gate:** `a` is a fixed-seed (`random.Random(42)`) array of
  **N = 120 000** non-negative integers with values in `0..1000`, and `k` is the
  middle rank `k = (N*(N+1)//2) // 2`. The call must complete within
  **8 seconds** (`gu.run_within(8.0, ...)`).
  * The O(n log(totalSum)) gold finishes in well under 1 second (comfortably more
    than 3x headroom).
  * The O(n^2) enumerate-and-sort would enumerate `N*(N+1)/2 ≈ 7.2 × 10^9`
    subarray sums — many minutes of work (and tens of GB of memory) — so it times
    out by orders of magnitude.

## Examples

```python
# Single element: only one subarray, k must be 1.
kth_subarray_sum([7], 1) == 7

# a = [1, 2, 3]; subarray sums:
#   [1]=1, [1,2]=3, [1,2,3]=6, [2]=2, [2,3]=5, [3]=3
# sorted multiset = [1, 2, 3, 3, 5, 6]
kth_subarray_sum([1, 2, 3], 1) == 1   # smallest
kth_subarray_sum([1, 2, 3], 4) == 3   # ties (two subarrays sum to 3) count twice
kth_subarray_sum([1, 2, 3], 6) == 6   # largest == sum(a)

# All-equal array a = [2, 2, 2]; sorted sums = [2, 2, 2, 4, 4, 6]
kth_subarray_sum([2, 2, 2], 3) == 2
kth_subarray_sum([2, 2, 2], 5) == 4

# Zeros allowed: a = [0, 0, 5]; subarray sums = [0,0,5,0,5,5] -> sorted [0,0,0,5,5,5]
kth_subarray_sum([0, 0, 5], 1) == 0
kth_subarray_sum([0, 0, 5], 4) == 5
```

## Constraints

* `1 <= n <= 120 000`
* All elements are non-negative integers (`a[i] >= 0`)
* `1 <= k <= n*(n+1)/2`
* Return a plain Python `int`.
