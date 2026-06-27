# Competitive 08 — `min_unstable_partition`: fewest stable segments, lex-smallest cuts

**Created:** 2026-06-17 · **Category:** competitive · **Weight:** 8

Partition a sequence into **contiguous, non-empty segments** so that within every
segment `max - min <= K`. Among **all partitions using the fewest possible
segments**, return the one whose list of segment **end indices** is
**lexicographically smallest**.

The difficulty is that these are two coupled requirements: the minimum *count* is
easy to get by a greedy sweep, but that greedy yields the lexicographically
*largest* cuts — the opposite of what is asked. You must achieve the minimum count
**and** push every cut as early as the count allows.

Implement your solution in a single file `solution.py` using the **standard
library only**.

## Public contract

### `min_unstable_cuts(values: list[int], K: int) -> list[int]`

- `values` has length `n >= 1`; `K >= 0` is the stability threshold.
- Consider partitions of `values` into consecutive non-empty segments such that
  each segment's `max - min <= K`. Let `m` be the **minimum** number of segments
  over all such partitions.
- Among **all** partitions that use exactly `m` segments, consider each one's list
  of segment **end indices** (0-based, inclusive, ascending; the last is always
  `n-1`). Return the **lexicographically smallest** such list.

A single element is always a valid segment (`max - min = 0 <= K`), so a partition
always exists.

**Edge cases (state-pinned).**

| Input | Result |
|-------|--------|
| `n == 1` | `[0]` |
| all elements equal | `[n-1]` (one segment) |
| strictly increasing with `K == 0` | `[0, 1, …, n-1]` (every element its own segment) |

## Worked example

`values = [1, 2, 3, 4]`, `K = 2`. The minimum number of segments is **2**. The
partitions achieving 2 segments, by their end-index lists, are:

* `[0, 3]` → `[1] | [2,3,4]` (spans 2..4 → max-min = 2 ✓)
* `[1, 3]` → `[1,2] | [3,4]`
* `[2, 3]` → `[1,2,3] | [4]`

The lexicographically smallest is **`[0, 3]`**. (A greedy "extend each segment as
far as possible" returns `[2, 3]` — the correct count but the wrong, largest cuts.)

## Performance contract (hard gate)

`n` can be as large as **100 000**. The grader runs a fixed-seed instance at
`n = 100_000` and requires the call to return **within 4 seconds**. Recomputing a
segment's `max - min` from scratch for each candidate split is `Θ(n²)` and cannot
meet this budget; an `O(n log n)` (or better) approach is required.

## Notes

* The function is **pure**: it must not mutate `values`.
* Determinism: the answer is fully determined by `(values, K)`; no seeds, no I/O.
