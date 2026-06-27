"""Graph data structure implementation."""

from collections import defaultdict


class Graph:
    """A weighted graph that can be directed or undirected."""

    def __init__(self, directed: bool = False):
        self.directed = directed
        # adjacency: node -> list of (neighbor, weight)
        self._adj = {}
        self._edge_count = 0

    def add_node(self, n) -> None:
        """Add a node; no-op if already present."""
        if n not in self._adj:
            self._adj[n] = []

    def add_edge(self, u, v, weight: float = 1.0) -> None:
        """Add an edge (and both endpoints).
        For undirected graphs the edge is bidirectional.
        """
        self.add_node(u)
        self.add_node(v)
        self._adj[u].append((v, weight))
        self._edge_count += 1
        if not self.directed and u != v:
            self._adj[v].append((u, weight))

    def neighbors(self, n):
        """Return an iterable of (neighbor, weight) pairs for node n."""
        return self._adj.get(n, [])

    @property
    def num_nodes(self) -> int:
        """Number of distinct nodes."""
        return len(self._adj)

    @property
    def num_edges(self) -> int:
        """Number of edges (each undirected edge counts once)."""
        return self._edge_count

    def nodes(self):
        """Return all nodes."""
        return self._adj.keys()
