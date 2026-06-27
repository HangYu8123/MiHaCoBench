"""
structures.py — Graph data structure supporting directed and undirected graphs.
"""


class Graph:
    """Adjacency-dict graph.

    Parameters
    ----------
    directed : bool
        If True, edges are one-directional. If False (default), each add_edge
        call mirrors the edge in both directions in the internal adjacency dict,
        but num_edges counts each undirected edge once.
    """

    def __init__(self, directed: bool = False) -> None:
        self._directed: bool = directed
        # _adj[u][v] = weight
        self._adj: dict = {}
        self._num_edges: int = 0

    # ------------------------------------------------------------------
    # Node / edge mutation
    # ------------------------------------------------------------------

    def add_node(self, n) -> None:
        """Add a node; no-op if already present."""
        if n not in self._adj:
            self._adj[n] = {}

    def add_edge(self, u, v, weight: float = 1.0) -> None:
        """Add an edge (and both endpoints).

        For undirected graphs the edge is bidirectional in _adj but counted
        once in num_edges.  Re-adding an existing edge updates the weight
        without incrementing the edge counter.
        """
        # Ensure both nodes exist
        self.add_node(u)
        self.add_node(v)

        if self._directed:
            # Check if this is a new edge
            is_new = v not in self._adj[u]
            self._adj[u][v] = weight
            if is_new:
                self._num_edges += 1
        else:
            # For undirected: a self-loop writes only one slot (_adj[u][u]).
            # For a regular edge: two slots but counted once.
            is_new = v not in self._adj[u]
            self._adj[u][v] = weight
            if u != v:
                self._adj[v][u] = weight
            if is_new:
                self._num_edges += 1

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def neighbors(self, n):
        """Return iterable of (neighbor, weight) pairs for node n."""
        return list(self._adj.get(n, {}).items())

    @property
    def num_nodes(self) -> int:
        return len(self._adj)

    @property
    def num_edges(self) -> int:
        return self._num_edges
