# Competitive 04 — `sum_of_distances`: Sum of Weighted Distances in a Tree

**Created:** 2026-06-15 · **Category:** competitive · **Weight:** 8

Implement a **single file** `solution.py` (standard library only) that computes,
for every node in a weighted undirected tree, the sum of distances to all other
nodes.

## Public contract

```python
def sum_of_distances(n: int, edges: list[tuple]) -> list[int]:
    """Return res where res[i] = sum of weighted distances from node i to ALL other nodes.

    Parameters
    ----------
    n : int
        Number of nodes, 0-indexed: nodes are labelled 0, 1, ..., n-1.
    edges : list[tuple]
        List of n-1 undirected weighted edges, each a tuple (u, v, w) where
        u and v are node indices (0-indexed) and w is a positive integer weight.
        The edges form a valid tree (connected, no cycles).

    Returns
    -------
    list[int]
        A list of n integers: res[i] is the sum of weighted distances from
        node i to every other node j != i.  For n == 1, return [0].

    Notes
    -----
    * Edge weight w contributes w to the distance along that edge.
    * All weights are positive integers.
    * n == 1 is a valid input (single node, no edges): return [0].
    * The function must run in O(n) time (two-pass rerooting DP, iterative).
      A naïve O(n^2) approach (Dijkstra/BFS from each node) will time out on
      the hard complexity gate: n = 200 000 within 15 seconds.
    """
```

## Algorithm requirement (hard-gated)

| Requirement | Detail |
|---|---|
| **Time** | O(n) — two-pass rerooting tree DP. A naïve BFS/Dijkstra from each node costs O(n^2) and will time out on large inputs. |
| **Implementation** | Must use **iterative** DFS (avoid Python's default recursion limit on deep/caterpillar trees). |

### Concrete gate values (in the grader)

* **Hard time gate:** `n = 200 000` (randomly built tree, fixed seed) — must complete
  within **15 seconds**.  An O(n^2) approach would require on the order of
  200 000 × 200 000 / 2 ≈ 2 × 10^10 operations and would take many minutes.

## Examples

```python
# n=1: single node, no edges
sum_of_distances(1, []) == [0]

# n=2: one edge of weight 3
sum_of_distances(2, [(0, 1, 3)]) == [3, 3]

# Path 0-1-2 with weights 1 and 2
# dist(0,1)=1, dist(0,2)=3 -> res[0]=4
# dist(1,0)=1, dist(1,2)=2 -> res[1]=3
# dist(2,0)=3, dist(2,1)=2 -> res[2]=5
sum_of_distances(3, [(0, 1, 1), (1, 2, 2)]) == [4, 3, 5]

# Star graph: center=0, leaves=1,2,3 all weight 1
# res[0] = 1+1+1 = 3; res[1]=1+2+2=5; etc.
sum_of_distances(4, [(0, 1, 1), (0, 2, 1), (0, 3, 1)]) == [3, 5, 5, 5]
```

## Constraints

* `1 ≤ n ≤ 200 000`
* Edges form a valid tree (exactly n-1 undirected edges, connected)
* All weights are positive integers (w ≥ 1)
* Return a plain Python `list[int]` of length n
