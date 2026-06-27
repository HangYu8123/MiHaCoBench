"""Graph data structure."""


class Graph:
    """Adjacency-dict based graph.

    Parameters
    ----------
    directed : bool
        If True the graph is directed; otherwise undirected.
    """

    def __init__(self, directed: bool = False):
        self._directed = directed
        self._adj: dict = {}   # {node: {neighbor: weight}}
        self._edge_count: int = 0  # unique edges

    # ------------------------------------------------------------------
    # Node / edge manipulation
    # ------------------------------------------------------------------

    def add_node(self, n) -> None:
        """Add a node; no-op if already present."""
        if n not in self._adj:
            self._adj[n] = {}

    def add_edge(self, u, v, weight: float = 1.0) -> None:
        """Add an edge (and both endpoints).

        For undirected graphs the edge is bidirectional.
        Repeated calls with the same (u, v) overwrite weight without
        incrementing the edge count.
        """
        # Ensure both nodes exist
        self.add_node(u)
        self.add_node(v)

        if self._directed:
            is_new = v not in self._adj[u]
            self._adj[u][v] = weight
            if is_new:
                self._edge_count += 1
        else:
            # For undirected: a self-loop (u==v) is stored once
            if u == v:
                is_new = v not in self._adj[u]
                self._adj[u][v] = weight
                if is_new:
                    self._edge_count += 1
            else:
                is_new = v not in self._adj[u]
                self._adj[u][v] = weight
                self._adj[v][u] = weight
                if is_new:
                    self._edge_count += 1

    # ------------------------------------------------------------------
    # Accessors
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
        """Number of edges (each undirected edge counted once)."""
        return self._edge_count
