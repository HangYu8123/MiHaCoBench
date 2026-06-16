# Compositional 07 — `graph_spectral`: Graph Laplacian Spectral Partition

**Created:** 2026-06-16 · **Category:** compositional · **Weight:** 4

Implement a function that performs a **spectral partition** of an undirected
weighted graph by composing **networkx** (graph construction + Laplacian),
**scipy.linalg** (symmetric eigendecomposition), and **numpy** (array work).
Write your solution as `solution.py`.

## Public contract

```python
def spectral_partition(edges: list[tuple], n: int) -> dict:
    ...
```

* `n` is the number of nodes; nodes are the integers `0, 1, ..., n-1`.
* `edges` is a list of `(u, v, w)` tuples describing an **undirected** graph,
  where `0 <= u, v < n` and `w` is a **positive** edge weight. Isolated nodes
  (nodes that appear in no edge) are allowed.

The function must:

1. Build a `networkx.Graph` containing **all** `n` nodes
   (`add_nodes_from(range(n))`) plus the weighted edges (store the weight under
   the `weight` attribute).
2. Form the **combinatorial Laplacian** `L = D - A` as a **dense** numpy array
   using a **fixed** node ordering:
   `networkx.laplacian_matrix(G, nodelist=range(n), weight="weight").toarray()`.
3. Compute the eigenvalues and eigenvectors of `L` with `scipy.linalg.eigh`
   (symmetric solver), and **sort them ascending** by eigenvalue.
4. Read off the **Fiedler value** and **Fiedler vector** — the
   **second-smallest** eigenvalue and its eigenvector.

Return a `dict` with **exactly** these keys (no extras, no missing):

| Key | Type | Meaning |
|---|---|---|
| `fiedler_value` | `float` | The **second-smallest** eigenvalue (the algebraic connectivity). |
| `partition` | `list[int]` | Length `n`. Entry `i` is `0` if the corresponding Fiedler-vector entry is `>= 0`, else `1`. |
| `connected` | `bool` | `True` iff the graph is connected, i.e. the **second-smallest** eigenvalue `> 1e-8`. |
| `n_components` | `int` | Number of connected components = number of eigenvalues `< 1e-8`. |

## Exception contract

Raise `ValueError` if any of the following hold:

* `n < 1`.
* An edge references a node index outside `[0, n)` (i.e. `u < 0`, `u >= n`,
  `v < 0`, or `v >= n`).
* An edge has a **non-positive** weight (`w <= 0`).

## Notes

* `fiedler_value` is the entry at **index 1** of the ascending-sorted
  eigenvalues — the SECOND smallest, **not** the smallest (the smallest is
  always ~0 for any graph). For a **connected** graph this equals
  `networkx.algebraic_connectivity(G, weight="weight")` within tolerance and is
  strictly positive.
* `connected` and `n_components` are derived from the eigenvalue spectrum: a
  graph with `k` connected components has exactly `k` eigenvalues equal to 0
  (use the threshold `1e-8`).
* Floats in the returned dict are compared by the grader with a tolerance — do
  not round.
* `connected` must be a Python `bool` and `n_components` a Python `int` (not
  numpy scalar types). `fiedler_value` must be a Python `float`.
