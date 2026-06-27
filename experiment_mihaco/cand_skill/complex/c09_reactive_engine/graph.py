"""
graph.py — DependencyGraph: a networkx DiGraph wrapper.

Edge direction: dep -> name  (dependency points to dependent).
This means nx.descendants(G, name) returns all transitive dependents of name.
"""

import networkx as nx


class DependencyGraph:
    """
    Wraps a networkx DiGraph where edges go  dep -> dependent.

    So if B depends on A we store the edge A -> B.
    nx.descendants(G, 'A') then gives {'B', ...} — all cells that
    (transitively) need A.
    """

    def __init__(self):
        self._g = nx.DiGraph()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _predecessors_of(self, name):
        """Return list of current deps (predecessors) for *name*."""
        if name in self._g:
            return list(self._g.predecessors(name))
        return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_edges(self, name, new_deps):
        """
        Update the dependency edges for *name* to *new_deps*.

        Strategy (atomic rollback):
          1. Record old predecessors.
          2. Remove old dep->name edges.
          3. Add new dep->name edges.
          4. Check DAG.  If cycle found: restore, raise ValueError.

        Returns the old list of deps so the caller can also snapshot
        _cells if needed.
        """
        old_deps = self._predecessors_of(name)

        # Remove old incoming edges
        self._g.remove_edges_from([(d, name) for d in old_deps])

        # Add new incoming edges (ensure node exists even if dep list empty)
        if not self._g.has_node(name):
            self._g.add_node(name)

        self._g.add_edges_from([(d, name) for d in new_deps])

        # Cycle check
        if not nx.is_directed_acyclic_graph(self._g):
            # Rollback
            self._g.remove_edges_from([(d, name) for d in new_deps])
            self._g.add_edges_from([(d, name) for d in old_deps])
            raise ValueError(
                f"Setting formula for '{name}' with deps {new_deps} "
                "would introduce a cycle."
            )

        return old_deps

    def ensure_node(self, name):
        """Make sure *name* exists as a node (no edges)."""
        if not self._g.has_node(name):
            self._g.add_node(name)

    def remove_incoming_edges(self, name):
        """
        Remove only the incoming edges (dep -> name) for *name*.
        Used when a formula cell is redefined as a constant cell.
        """
        if name in self._g:
            preds = list(self._g.predecessors(name))
            self._g.remove_edges_from([(p, name) for p in preds])

    def remove_node(self, name):
        """Remove node and ALL its incident edges."""
        if self._g.has_node(name):
            self._g.remove_node(name)

    def transitive_dependents(self, name):
        """
        Return the set of all cells that (transitively) depend on *name*.
        Edges go dep -> dependent, so descendants = dependents.
        """
        if not self._g.has_node(name):
            return set()
        return nx.descendants(self._g, name)

    def topological_sort(self):
        """Return a topologically sorted list of all nodes."""
        return list(nx.topological_sort(self._g))
