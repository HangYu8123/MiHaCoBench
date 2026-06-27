# Harness 01 — `apportion_seats`: Largest-Remainder Seat Apportionment

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 5

Allocate a fixed number of seats among parties in proportion to their vote
counts using the **largest-remainder (Hamilton / Hare-Niemeyer) method**. The
difficulty is entirely in the **exactness**: the result must sum to *exactly*
`total_seats`, the leftover seats are distributed by a precise remainder
ranking, and ties in that ranking are broken by a fixed rule — all decided with
exact arithmetic so no floating-point rounding can mis-order a tie.

Implement your solution in a single file `solution.py`. It uses only the Python
standard library (no third-party packages).

## Public contract

### `apportion(votes: list[int], total_seats: int) -> list[int]`

Return a list of seat counts, the **same length and order as `votes`**, that
sums to **exactly** `total_seats`.

The allocation is the largest-remainder method, defined exactly as:

1. Let `V = sum(votes)`. The **exact quota** of party `i` is the rational number
   `q_i = votes_i * total_seats / V`. Do **not** round it yet.
2. Each party first receives the **floor** of its quota: `base_i = floor(q_i)`.
3. Let `R = total_seats - sum(base_i)` be the number of leftover seats. (It is
   always an integer with `0 <= R <= len(votes)`.)
4. Distribute the `R` leftover seats, **one each**, to the `R` parties with the
   **largest fractional remainder** `r_i = q_i - base_i`.
5. **Tie-break** when two parties have equal remainders `r_i`: the party with the
   **larger `votes_i`** receives the seat first; if `votes_i` is also equal, the
   party with the **smaller index** receives it first.

The final seat count of party `i` is `base_i` plus one if it was awarded a
leftover seat, else `base_i`.

Use **exact integer / rational arithmetic** (e.g. compare remainders via
cross-multiplication, or `fractions.Fraction`) so that no floating-point error
can mis-order an exact tie.

### Exception contract

| Condition | Raise |
|-----------|-------|
| `total_seats < 0` | `ValueError` |
| any `votes_i < 0` | `ValueError` |
| `total_seats > 0` and `sum(votes) == 0` (including an empty `votes`) | `ValueError` |

When `total_seats == 0`, return a list of zeros of length `len(votes)` (this is
**not** an error, even when `votes` is empty — the result is then `[]`).

Assert exception **types**; messages are unspecified.

## Worked examples

```python
apportion([34, 33, 33], 10) == [4, 3, 3]
# quotas 3.4, 3.3, 3.3; base [3,3,3] sums to 9; one leftover seat goes to the
# largest remainder (0.4) -> party 0.

apportion([1, 1, 1], 2) == [1, 1, 0]
# quotas all 2/3; base [0,0,0] sums to 0; two leftover seats; remainders are all
# equal and votes are all equal, so they go by smaller index -> parties 0 and 1.

apportion([10, 20, 30, 40], 10) == [1, 2, 3, 4]
# exact quotas 1,2,3,4; base sums to 10; no leftover seats.

apportion([1, 1, 4], 4) == [1, 0, 3]
# quotas 2/3, 2/3, 8/3; base [0,0,2] sums to 2; two leftover seats; remainders
# are all equal at 2/3, so the larger-votes party 2 wins the first seat (-> 3),
# then equal-votes parties 0 and 1 are ranked by index, so party 0 wins the
# second seat (-> 1).
```

## Notes

* The function is **pure**: it must not mutate `votes`.
* The result is fully determined by `votes` and `total_seats`; no seeds are
  needed.
* `sum(apportion(votes, total_seats)) == total_seats` whenever the call does not
  raise, and `len(apportion(votes, total_seats)) == len(votes)` always.
