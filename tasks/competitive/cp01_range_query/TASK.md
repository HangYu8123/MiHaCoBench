# Competitive 01 — `process_queries`: Range Update / Range Sum

**Created:** 2026-06-15 · **Category:** competitive · **Weight:** 8

Implement a **single file** `solution.py` (standard library only) that maintains
an array of `n` integers (initially all zeros) and processes a sequence of
range-update and range-sum queries efficiently.

## Public contract

```python
def process_queries(n: int, ops: list[tuple]) -> list[int]:
    """Process a sequence of range operations on an array of n zeros.

    Each element of ops is one of:
      ("add", l, r, v)  — add integer v to every index in [l, r] inclusive (0-indexed)
      ("sum", l, r)     — return the current sum of elements at indices [l, r] inclusive

    Return a list of integers: one result per "sum" operation, in order.

    Parameters
    ----------
    n   : int   — length of the array; indices are 0-indexed: [0, n-1]
    ops : list  — list of operation tuples as described above

    Returns
    -------
    list[int]   — results of all "sum" queries, in the order they appear in ops
    """
```

### Operation types

| Tuple form | Meaning |
|---|---|
| `("add", l, r, v)` | Add `v` to every element at index `l, l+1, ..., r` (inclusive, 0-indexed). `v` may be negative. |
| `("sum", l, r)` | Return the sum of `arr[l] + arr[l+1] + ... + arr[r]` (inclusive, 0-indexed). |

### Constraints

* `1 ≤ n ≤ 200 000`
* `0 ≤ l ≤ r < n` for every operation
* `v` is a Python `int` (may be negative or zero)
* `ops` may contain up to `200 000` operations
* The function must return a plain Python `list[int]`

## Complexity requirements (hard-gated in the grader)

| Requirement | Detail |
|---|---|
| **Time** | O((n + q) log n) — range updates and range sums must both run in O(log n). A naïve O(n) per-operation loop is **not acceptable** and will time out on large inputs. |

### Concrete gate values (in the grader)

* **Hard time gate:** `n = 200 000`, `q ≈ 200 000` interleaved add/sum operations
  with a fixed seed `random.Random(1337)` — must complete within **10 seconds**.
  A naive O(N·Q) solution takes on the order of 200 000 × 200 000 / 2 ≈ 2 × 10¹⁰
  iterations (many minutes), so only an O((n + q) log n) implementation passes.
  (Both a dual-Fenwick BIT and a lazy-propagation segment tree comfortably fit
  this budget.)

## Implementation note (not required to read, but informative)

Range update + range sum requires more than the textbook point-update Fenwick
tree. Two common correct approaches:

1. **Dual Fenwick BIT** — maintain two trees `B1` and `B2` such that the prefix
   sum `[0..i]` equals `B1.query(i) * i - B2.query(i)`. Range updates become
   two point updates in each tree; range sums become two prefix-sum lookups.
2. **Lazy-propagation segment tree** — standard segtree with lazy tags for
   pending range additions.

The grader does not care which approach you use, only that the contract above
is satisfied and the hard time gate is met.

## Examples

```python
# Array of 5 zeros: [0, 0, 0, 0, 0]
ops = [
    ("add", 0, 4, 1),   # [1, 1, 1, 1, 1]
    ("sum", 0, 4),       # returns 5
    ("add", 1, 3, 2),   # [1, 3, 3, 3, 1]
    ("sum", 1, 3),       # returns 9
    ("sum", 0, 0),       # returns 1
]
assert process_queries(5, ops) == [5, 9, 1]

# Single element
ops2 = [("add", 0, 0, 7), ("sum", 0, 0)]
assert process_queries(1, ops2) == [7]

# No sum queries
assert process_queries(3, [("add", 0, 2, 5)]) == []

# Empty ops
assert process_queries(10, []) == []
```
