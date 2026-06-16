# Competitive 06 — `range_distinct`: offline distinct-count range queries

**Created:** 2026-06-16 · **Category:** competitive · **Weight:** 8

Implement a **single file** `solution.py` (standard library only) that answers
many "how many distinct values in this subarray" queries efficiently.

## Public contract (must match exactly)

```python
def range_distinct(a: list[int], queries: list[tuple]) -> list[int]:
    """Answer offline range-distinct-count queries.

    Parameters
    ----------
    a : list[int]
        The array of values (any hashable ints), length n >= 1.
    queries : list[tuple]
        A list of ``(l, r)`` pairs, each a **0-indexed INCLUSIVE** range with
        ``0 <= l <= r < n``.

    Returns
    -------
    list[int]
        One integer per query, in the **same order as the input queries**: the
        number of DISTINCT values in ``a[l..r]`` (inclusive).
    """
```

## Algorithm requirement (hard-gated)

| Requirement | Detail |
|---|---|
| **Time** | `O((n + q) log n)`. Process the queries **offline** (e.g. sort by right endpoint and sweep with a Fenwick/BIT using the last-occurrence trick). |
| **Forbidden by feasibility** | A naive `len(set(a[l:r+1]))` per query is `O(n·q)` and **times out** on the gate. |

### Concrete gate values (in the grader)

* **Hard time gate:** `n = 150000`, `q = 150000` (fixed-seed random array + queries) —
  must complete within **8 seconds**. The naive per-query approach would need on the
  order of `1.5e5 × 1.5e5 ≈ 2.25 × 10^10` operations and times out.

## Examples

```python
range_distinct([1, 1, 2, 1, 3], [(0, 1), (0, 4), (2, 4)]) == [1, 3, 3]
range_distinct([5, 5, 5], [(0, 2), (1, 1)])               == [1, 1]
```

## Constraints

* `1 <= n`; every query satisfies `0 <= l <= r < n`.
* Results must be returned in the **same order** as the input `queries` list.
* Return a plain `list[int]`.
