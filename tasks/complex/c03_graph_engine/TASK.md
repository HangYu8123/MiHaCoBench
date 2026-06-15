# Complex 03 — `graph_engine`: Graph Data Structure and Classic Algorithms

**Created:** 2026-06-15 · **Category:** complex · **Weight:** 5

Implement a small graph engine spread across multiple files. Your solution must
use **numpy** (for PageRank's linear-algebra work) and **networkx** (optionally,
for cross-checking — but you must implement the algorithms yourself). Write your
solution as a multi-file package. The grader loads modules by path.

## Files to create

```
structures.py    — class Graph
traversal.py     — bfs, dijkstra, connected_components
ranking.py       — pagerank, degree_centrality
graph_engine.py  — FACADE: re-exports all public names from the three files above
```

---

## Public contract (every name must be importable from `graph_engine.py`)

### `class Graph(directed: bool = False)`

| Method / Attribute | Signature | Notes |
|---|---|---|
| `add_node(n)` | `add_node(self, n) -> None` | Add a node; no-op if already present. |
| `add_edge(u, v, weight=1.0)` | `add_edge(self, u, v, weight: float = 1.0) -> None` | Add an edge (and both endpoints). For undirected graphs the edge is bidirectional. |
| `neighbors(n)` | `neighbors(self, n) -> Iterable` | Return an iterable of `(neighbor, weight)` pairs for node `n`. |
| `num_nodes` | property or attribute `int` | Number of distinct nodes. |
| `num_edges` | property or attribute `int` | Number of edges (each undirected edge counts once). |

### `bfs(graph, source) -> dict[node, int]`

Breadth-first traversal from `source`. Returns a dict mapping each **reachable**
node (including `source`) to its hop distance (number of edges). `source` maps to
`0`. Unreachable nodes are **omitted**.

### `dijkstra(graph, source) -> dict[node, float]`

Shortest-path distances (by edge weight sum) from `source` to every **reachable**
node. Returns `{node: distance}`. `source` maps to `0.0`. Unreachable nodes are
**omitted**. Uses the `weight` stored on each edge.

### `connected_components(graph) -> list[set]`

For **undirected** graphs only. Returns a list of sets, where each set contains
the nodes of one connected component. Order of the list and order within each set
are unspecified.

### `pagerank(graph, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-9) -> dict[node, float]`

Compute the PageRank of every node. The returned dict must:
- contain every node in the graph,
- have values summing to approximately 1.0 (within 1e-6),
- converge within `max_iter` power-iterations.

Implement the standard power-iteration algorithm. The damping factor `d` is used
as: `PR(v) = (1-d)/N + d * Σ PR(u)/out_degree(u)` for each in-neighbour `u`.

### `degree_centrality(graph) -> dict[node, float]`

Return `{node: degree / (N-1)}` where `N` is the total number of nodes. For
directed graphs, use the **total degree** (in + out). For `N <= 1`, return
`{node: 0.0}` for all nodes. Every node in the graph must appear in the result.

---

## Notes

- Node identifiers may be any hashable Python value (int, str, etc.).
- Self-loops are allowed (an edge `u -> u`).
- All numeric edge weights are positive floats.
- The grader imports from `graph_engine.py` only; it does not care about internal
  module structure.
- Determinism: given the same graph and seed, `pagerank` must produce identical
  results across runs.
