"""
structures.py — class Graph
"""
from __future__ import annotations
from typing import Iterable, Tuple, Any


class Graph:
    """
    A weighted graph that can be either directed or undirected.

    Parameters
    ----------
    directed : bool
        If True the graph is directed; if False (default) edges are bidirectional.
    """

    def __init__(self, directed: bool = False) -> None:
        self._directed = directed
        # adjacency: {node: {neighbor: weight}}
        self._adj: dict = {}
        # For undirected graphs we need to track the logical edge count
        # (each undirected edge should count once).
        self._edge_count: int = 0

    # ------------------------------------------------------------------
    # Node / edge manipulation
    # ------------------------------------------------------------------

    def add_node(self, n: Any) -> None:
        """Add a node; no-op if already present."""
        if n not in self._adj:
            self._adj[n] = {}

    def add_edge(self, u: Any, v: Any, weight: float = 1.0) -> None:
        """
        Add a weighted edge from u to v.
        For undirected graphs the edge is bidirectional.
        Both endpoints are added automatically.
        """
        self.add_node(u)
        self.add_node(v)

        if self._directed:
            # Only add in the u -> v direction; track each directed edge.
            existed = v in self._adj[u]
            self._adj[u][v] = weight
            if not existed:
                self._edge_count += 1
        else:
            # Undirected: add both directions, but count as one edge.
            # Check if this undirected edge already existed.
            existed = v in self._adj[u]
            self._adj[u][v] = weight
            self._adj[v][u] = weight
            if not existed:
                self._edge_count += 1

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def neighbors(self, n: Any) -> Iterable[Tuple[Any, float]]:
        """Return an iterable of (neighbor, weight) pairs for node n."""
        return self._adj[n].items()

    @property
    def num_nodes(self) -> int:
        """Number of distinct nodes."""
        return len(self._adj)

    @property
    def num_edges(self) -> int:
        """
        Number of edges.
        For undirected graphs each edge is counted once.
        For directed graphs each directed arc is counted.
        """
        return self._edge_count

    # ------------------------------------------------------------------
    # Internals used by algorithm modules
    # ------------------------------------------------------------------

    @property
    def directed(self) -> bool:
        return self._directed

    def nodes(self):
        """Return all nodes."""
        return self._adj.keys()

    def all_edges(self):
        """
        Yield (u, v, weight) for every logical edge.
        For directed graphs yields every arc.
        For undirected graphs yields each edge once (u < v is not guaranteed
        for non-comparable types, so we use an id-based dedup).
        """
        seen = set()
        for u, nbrs in self._adj.items():
            for v, w in nbrs.items():
                if self._directed:
                    yield u, v, w
                else:
                    key = (id(u), id(v)) if id(u) <= id(v) else (id(v), id(u))
                    # Fall back to value-based key when possible
                    try:
                        key = (u, v) if u <= v else (v, u)
                    except TypeError:
                        key = (min(id(u), id(v)), max(id(u), id(v)))
                    if key not in seen:
                        seen.add(key)
                        yield u, v, w
