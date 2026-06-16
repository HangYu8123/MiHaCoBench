"""
structures.py — Graph data structure.
"""


class Graph:
    """Adjacency-dict graph. Supports directed and undirected, weighted edges."""

    def __init__(self, directed: bool = False) -> None:
        self.directed = directed
        self._adj: dict = {}       # node -> {neighbor: weight}
        self._edge_count: int = 0

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(self, n) -> None:
        """Add a node; no-op if already present."""
        if n not in self._adj:
            self._adj[n] = {}

    # ------------------------------------------------------------------
    # Edge management
    # ------------------------------------------------------------------

    def add_edge(self, u, v, weight: float = 1.0) -> None:
        """Add an edge (and both endpoints).

        For undirected graphs the edge is bidirectional and each undirected
        edge counts once toward num_edges (calling add_edge(u,v) and then
        add_edge(v,u) on the same undirected graph counts as one edge).
        """
        self.add_node(u)
        self.add_node(v)

        if self.directed:
            # Directed: only u -> v
            existed = v in self._adj[u]
            self._adj[u][v] = weight
            if not existed:
                self._edge_count += 1
        else:
            # Undirected: check both directions; they share one canonical edge.
            # The canonical form is: the edge exists iff v in _adj[u] (and
            # symmetrically u in _adj[v]).  Only count once.
            existed = v in self._adj[u]
            self._adj[u][v] = weight
            self._adj[v][u] = weight
            if not existed:
                self._edge_count += 1

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def neighbors(self, n):
        """Return an iterable of (neighbor, weight) pairs for node n."""
        return self._adj[n].items()

    @property
    def num_nodes(self) -> int:
        """Number of distinct nodes."""
        return len(self._adj)

    @property
    def num_edges(self) -> int:
        """Number of edges (each undirected edge counts once)."""
        return self._edge_count
