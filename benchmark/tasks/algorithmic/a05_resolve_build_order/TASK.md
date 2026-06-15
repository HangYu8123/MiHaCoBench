# Algorithmic 05 — `resolve_build_order`: Lexicographically-smallest topological sort

**Created:** 2026-06-15 · **Category:** algorithmic · **Weight:** 8 · **Difficulty:** hard

Implement a build-order resolver that, given `n` tasks and a list of dependency
edges, returns the lexicographically-smallest valid topological ordering using
**Kahn's algorithm** with a min-heap. Write your solution as a single file
`solution.py`. Use **stdlib only** (`heapq`, `collections`).

## Public contract (must match exactly)

```python
def resolve_build_order(n: int, deps: list[tuple[int, int]]) -> list[int]:
    ...
```

### Parameters

| Parameter | Type | Meaning |
|---|---|---|
| `n` | `int` | Number of tasks, labelled `0` through `n-1`. |
| `deps` | `list[tuple[int,int]]` | Dependency edges. A pair `(a, b)` means task `a` **must** complete before task `b`. May be empty. Self-loops `(a, a)` are valid inputs and indicate a cycle. |

### Return value

A `list[int]` containing a valid topological ordering of all `n` tasks
(every task appears exactly once).

**Tie-breaking rule:** when multiple tasks have no remaining unfulfilled
dependencies at the same time, always pick the **smallest index** first.
This produces the unique lexicographically-smallest topological order.

### Exception

Raise `ValueError` (any message) when the dependency graph contains a
**cycle** (i.e. a topological sort is impossible). A self-loop `(a, a)` is a
cycle. Duplicate edges are allowed and are treated as a single dependency.

## Complexity requirement

| Requirement | Value |
|---|---|
| Time complexity | O(V + E) where V = n, E = len(deps) |
| Hard timing gate | n = 200 000, ~400 000 edges, must finish within **5 seconds** |

The O(V + E) requirement rules out O(V·E) repeated-scan approaches.
Use **Kahn's algorithm**: maintain in-degree counts and a min-heap of
ready tasks; each edge and node is processed exactly once.

## Notes

* Determinism: identical `(n, deps)` ⇒ identical output.
* `deps` may contain duplicate edges; treat them as one edge.
* The returned list must contain **every** task label from 0 to n-1.
