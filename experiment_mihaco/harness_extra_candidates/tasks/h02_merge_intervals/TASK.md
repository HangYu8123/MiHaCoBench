# Harness 02 — `merge_intervals`: Coalesce Half-Open Intervals

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 4

Coalesce a list of **half-open** intervals into the minimal list of disjoint
intervals covering exactly the same set of points.

Implement your solution in a single file `solution.py`. Standard library only;
no third-party packages.

## Public contract

### `merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]`

Each input is a **half-open** interval `[start, end)` — it covers every point
`x` (think of `x` ranging over the integers, or the reals) with
`start <= x < end`. Return the **minimal** list of disjoint half-open intervals
covering **exactly the same point set**, sorted by `start` **ascending**. Each
output interval is an `(int, int)` tuple.

Rules:

1. **Half-open adjacency merges.** Because the intervals are half-open, `[1, 3)`
   and `[3, 5)` are contiguous — their union is exactly `[1, 5)` with no gap and
   no overlap — and MUST coalesce into `[1, 5)`. In general, two intervals
   coalesce iff the later one's `start` is `<=` the running end.
2. **Zero-length intervals are empty.** An interval with `start == end` covers
   **no points**; it must be **dropped** — it never appears in the output and
   never bridges a gap. (For example `[2, 2)` contributes nothing.)
3. The input may be **empty**, **unsorted**, contain **duplicates**, **nested**
   intervals, and **negative** coordinates.
4. If any interval has `start > end` (strictly), raise `ValueError`.
   (`start == end` is allowed — it is dropped per rule 2.)
5. The function is **pure**: it must not mutate the input list or any of its
   tuples.

Assert exception **types**; messages are unspecified.

## Worked examples

```
merge([(1, 3), (3, 5)])            == [(1, 5)]          # half-open adjacency merge
merge([(1, 5), (2, 3)])            == [(1, 5)]          # nested interval absorbed
merge([(5, 7), (1, 3)])            == [(1, 3), (5, 7)]  # real gap kept; output sorted
merge([(1, 4), (2, 2), (4, 6)])    == [(1, 6)]          # (2,2) dropped; (1,4)&(4,6) adjacency-merge
merge([(0, 0)])                    == []                # only an empty interval
merge([])                          == []                # empty input
```

## Notes

* The result must be the *minimal* cover: no two output intervals may be
  adjacent or overlapping (any such pair would itself coalesce).
* Determinism: the output is fully determined by the input point set; no seeds
  are needed.
