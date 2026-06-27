# Competitive 09 — `dependent_selection`: maximum-value selection under "requires" constraints

**Created:** 2026-06-17 · **Category:** competitive · **Weight:** 8

You are given `n` items, each with an integer **value** that may be **positive or
negative**. You may select any subset of items, **subject to dependency
constraints**: each constraint `(a, b)` means "if you select item `a`, you must
also select item `b`". Choose the subset that **maximizes the total value of the
selected items**.

Selecting nothing is always allowed (total value `0`), so the answer is never
negative.

Implement your solution in a single file `solution.py` using the **standard
library only**.

## Public contract

### `best_selection_value(values: list[int], requires: list[tuple[int, int]]) -> int`

- `values[i]` is the integer value of item `i` (items are `0 … n-1`); values may be
  negative.
- `requires` is a list of `(a, b)` pairs, each meaning **selecting `a` forces
  selecting `b`**. Constraints may chain (`a` requires `b`, `b` requires `c`) and
  may form cycles (`a` requires `b`, `b` requires `a` — then they are all-or-nothing
  together). Duplicate or self (`a == a`) constraints may appear and are harmless.
- Return the **maximum total value** over all subsets `S` such that for every
  `(a, b)` in `requires`, `a in S` implies `b in S`.

**Edge cases (state-pinned).**

| Input | Result |
|-------|--------|
| `n == 0` (no items) | `0` |
| all values `<= 0` | `0` (select nothing) |
| no constraints | the sum of all strictly-positive values |

## Worked example

`values = [10, -100]`, `requires = [(0, 1)]`:

Item 0 is worth `+10` but selecting it **requires** item 1, worth `-100`. The group
`{0, 1}` totals `-90`, so it is better to select **nothing** → answer **`0`**.
(Note: greedily "taking every positive item and pulling in its dependencies" would
select `{0, 1}` and report `-90` — that is wrong.)

`values = [10, 5, -3]`, `requires = [(0, 2)]`: best is `{0, 1, 2}` →
`10 + 5 - 3 = 12` (item 1 is free; item 0 pays for the `-3` dependency and still
nets positive) → answer **`12`**.

## Performance contract

`n` can be as large as **500** with up to a few thousand constraints. Searching over
subsets is exponential and infeasible beyond ~25 items; a **polynomial** algorithm
is required. The grader checks correctness at sizes where any exponential search
cannot finish.

## Notes

* The function is **pure**: it must not mutate `values` or `requires`.
* Determinism: the answer is fully determined by `(values, requires)`; no seeds, no I/O.
* All values fit in normal Python integers; the total fits in 64 bits.
