# Algorithmic 10 — `kth_distinct_in_window`: k-th distinct value per sliding window

**Created:** 2026-06-17 · **Category:** algorithmic · **Weight:** 8 · **Target complexity:** `O(n log V)`

Slide a fixed-width window across an array and, for each window, report the
**k-th smallest distinct value** inside it. Two things make this tricky: an
**inclusive count boundary** (a window with *exactly* `k` distinct values still
has a k-th distinct value) and a **performance gate** (rebuilding the distinct set
per window is too slow).

Implement your solution in a single file `solution.py` using the **standard
library only**.

## Public contract

### `kth_distinct_in_window(a: list[int], w: int, k: int) -> list`

- Consider every contiguous window `a[i : i+w]` (inclusive of indices `i` through
  `i+w-1`, exactly `w` elements), for `i = 0 … len(a)-w`.
- For each window, let `D` be the **sorted distinct values** present in it. The
  window's answer is:
  - the **k-th smallest** distinct value, `D[k-1]`, if the window has **at least
    `k`** distinct values (so a window with *exactly* `k` distinct values yields
    `D[k-1]`, its largest distinct value); otherwise
  - `None`, if the window has **fewer than `k`** distinct values.
- Return the list of per-window answers, in window order. Its length is
  `len(a) - w + 1`.

**Boundary / edge cases (state-pinned).**

| Input | Result |
|-------|--------|
| `w < 1` or `k < 1` | raise `ValueError` |
| `w > len(a)` (no full window fits) | `[]` |
| window has `< k` distinct values | `None` for that window |
| window has `== k` distinct values | the k-th (largest) distinct value — **not** `None` |

## Worked examples

`a = [3, 1, 2, 1, 3]`, `w = 3`, `k = 2`:

```
window [3,1,2] -> distinct sorted [1,2,3] -> 2nd = 2
window [1,2,1] -> distinct sorted [1,2]   -> exactly 2 distinct -> 2nd = 2   (NOT None)
window [2,1,3] -> distinct sorted [1,2,3] -> 2nd = 2
=> [2, 2, 2]
```

`a = [1, 2, 3, 1, 2, 3]`, `w = 3`, `k = 3`: every window has exactly 3 distinct
values, so each yields the 3rd (largest) = `3` → `[3, 3, 3, 3]`.

## Performance contract (hard gate)

`len(a)` can be as large as **200 000** with `w` up to a few thousand. The grader
runs a fixed-seed instance at `n = 200_000`, `w = 1000` and requires the call to
return **within 5 seconds**. Rebuilding each window's distinct set from scratch is
`Θ(n·w)` and cannot meet this budget; maintain the window incrementally.

## Notes

* The function is **pure**: it must not mutate `a`.
* Determinism: the answer is fully determined by `(a, w, k)`; no seeds, no I/O.
* Values may be any integers (negative, large); do not assume a small fixed range.
