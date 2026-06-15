"""Graph data structure for c03_graph_engine.

Supports both directed and undirected graphs with weighted edges.
Node identifiers can be any hashable Python value.
"""
from __future__ import annotations

from typing import Any, Iterable


class Graph:
    """Adjacency-list graph supporting directed and undirected weighted edges.

    Parameters
    ----------
    directed:
        If ``True``, edges are one-way (u -> v only). If ``False`` (default),
        ``add_edge(u, v)`` creates edges in both directions with the same weight.
    """

    def __init__(self, directed: bool = False) -> None:
        self._directed: bool = directed
        # _adj maps node -> {neighbor: weight}
        self._adj: dict[Any, dict[Any, float]] = {}
        # Track number of edges explicitly (each undirected edge counted once)
        self._edge_count: int = 0

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #

    def add_node(self, n: Any) -> None:
        """Add node *n*; no-op if it already exists."""
        if n not in self._adj:
            self._adj[n] = {}

    def add_edge(self, u: Any, v: Any, weight: float = 1.0) -> None:
        """Add an edge from *u* to *v* with the given *weight*.

        Both endpoints are created if they do not exist. For undirected graphs
        the reverse edge ``v -> u`` is also added with the same weight.
        Duplicate edges (same ``u, v`` pair) overwrite the previous weight;
        the edge count is only incremented for genuinely new edges.
        """
        self.add_node(u)
        self.add_node(v)

        # Directed case
        is_new = v not in self._adj[u]
        self._adj[u][v] = float(weight)
        if is_new:
            self._edge_count += 1

        if not self._directed and u != v:
            # Undirected: mirror edge; edge_count already incremented above
            self._adj[v][u] = float(weight)

    # ------------------------------------------------------------------ #
    # Inspection
    # ------------------------------------------------------------------ #

    def neighbors(self, n: Any) -> Iterable[tuple[Any, float]]:
        """Return ``(neighbor, weight)`` pairs for node *n*.

        Raises ``KeyError`` if *n* is not in the graph.
        """
        if n not in self._adj:
            raise KeyError(f"Node {n!r} not in graph")
        return self._adj[n].items()

    @property
    def num_nodes(self) -> int:
        """Number of distinct nodes in the graph."""
        return len(self._adj)

    @property
    def num_edges(self) -> int:
        """Number of edges.

        Each undirected edge is counted once; directed edges each count once.
        """
        return self._edge_count

    # ------------------------------------------------------------------ #
    # Iteration helpers used by algorithms
    # ------------------------------------------------------------------ #

    def nodes(self) -> Iterable[Any]:
        """Iterate over all nodes."""
        return self._adj.keys()

    def edges(self) -> Iterable[tuple[Any, Any, float]]:
        """Iterate over ``(u, v, weight)`` triples.

        For undirected graphs each undirected edge appears twice (once per
        direction) — callers that need the unique set should deduplicate.
        """
        for u, nbrs in self._adj.items():
            for v, w in nbrs.items():
                yield u, v, w

    @property
    def is_directed(self) -> bool:
        """``True`` if this is a directed graph."""
        return self._directed
