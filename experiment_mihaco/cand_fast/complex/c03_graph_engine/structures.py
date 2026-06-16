"""structures.py — Graph data structure."""

from collections import defaultdict


class Graph:
    """A weighted graph supporting directed and undirected edges."""

    def __init__(self, directed: bool = False):
        self._directed = bool(directed)
        # adjacency: node -> {neighbor: weight}
        self._adj = defaultdict(dict)
        # set of all nodes
        self._nodes = set()
        # edge tracking for num_edges (dedup)
        # directed: set of (u, v) tuples
        # undirected: set of frozenset({u, v}) — but self-loops stored as frozenset({u})
        self._edge_set = set()

    def add_node(self, n) -> None:
        """Add a node; no-op if already present."""
        self._nodes.add(n)

    def add_edge(self, u, v, weight: float = 1.0) -> None:
        """Add an edge and both endpoints."""
        self.add_node(u)
        self.add_node(v)

        if self._directed:
            self._adj[u][v] = weight
            edge_key = (u, v)
        else:
            self._adj[u][v] = weight
            if u != v:
                self._adj[v][u] = weight
            # For undirected, key is a frozenset (handles u==v as frozenset({u}))
            edge_key = frozenset((u, v))

        self._edge_set.add(edge_key)

    def neighbors(self, n):
        """Return an iterable of (neighbor, weight) pairs for node n."""
        if n not in self._nodes:
            return {}.items()
        return self._adj[n].items()

    @property
    def num_nodes(self) -> int:
        """Number of distinct nodes."""
        return len(self._nodes)

    @property
    def num_edges(self) -> int:
        """Number of edges (each undirected edge counts once)."""
        return len(self._edge_set)
