# Competitive 07 — `path_xor_sum`: Sum of path XORs over all node pairs in a tree

**Created:** 2026-06-17 · **Category:** competitive · **Weight:** 8

You are given an undirected, connected, weighted **tree**. For every unordered
pair of distinct nodes `(a, b)`, the unique path between them has a value equal to
the **XOR** of the weights of the edges on that path. Compute the **sum of that
value over all pairs**, taken **modulo 1 000 000 007**.

Implement your solution in a single file `solution.py` using the **standard
library only**.

## Public contract

### `sum_path_xor(n: int, edges: list[tuple[int, int, int]]) -> int`

- `n` is the number of nodes, labelled `0 .. n-1`. The graph is a tree, so there
  are **exactly `n - 1` edges** and it is connected.
- `edges` is a list of `(u, v, w)` triples, each an undirected edge between nodes
  `u` and `v` with integer weight `0 <= w < 2**30`.
- Return

  ```
  ( sum over all unordered pairs a < b of  pathxor(a, b) )  mod 1_000_000_007
  ```

  where `pathxor(a, b)` is the XOR of the weights of the edges on the unique path
  from `a` to `b`.

**Edge cases (state-pinned).**

| Input | Result |
|-------|--------|
| `n == 1` (no pairs) | `0` |
| `n == 2` (one edge of weight `w`) | `w % 1_000_000_007` |
| every edge weight `0` | `0` |

The reduction modulo `1_000_000_007` applies to the **final sum** (the per-pair
XOR values themselves are never reduced).

## Performance contract (hard gate)

`n` can be as large as **200 000**. The grader runs a fixed-seed instance at
`n = 200_000` and requires the call to return **within 5 seconds**. Enumerating all
`Θ(n²)` pairs explicitly cannot meet this budget — an efficient approach is
required. (Note: a recursive tree traversal will exceed Python's recursion limit
on a path-shaped tree of this size; iterate.)

## Notes

* The function is **pure**: it must not mutate `edges`.
* Determinism: the answer is fully determined by `(n, edges)`; no seeds, no I/O.
* You may assume the input always describes a valid tree (connected, `n-1` edges,
  weights in range); you need not validate it.
