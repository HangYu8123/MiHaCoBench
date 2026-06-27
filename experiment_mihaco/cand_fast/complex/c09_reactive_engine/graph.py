"""
graph.py — networkx DiGraph wrapper for dependency tracking.

Edge convention: dep -> cell  (meaning: cell depends on dep).
So nx.descendants(G, name) returns all cells that (transitively) depend on name.
"""
import networkx as nx


class DependencyGraph:
    """Wraps a networkx DiGraph to track cell dependencies."""

    def __init__(self):
        self._g = nx.DiGraph()

    # ------------------------------------------------------------------
    # Public API used by engine.py
    # ------------------------------------------------------------------

    def ensure_node(self, name):
        """Make sure the node exists in the graph (no-op if already present)."""
        if name not in self._g:
            self._g.add_node(name)

    def add_or_update_formula(self, name, deps):
        """
        Re-point the incoming edges of *name* to *deps*.

        Only removes/adds edges where *name* is the TARGET (i.e. name's own
        formula dependencies). Outgoing edges (cells that depend on name) are
        untouched.

        Raises ValueError if the new edges would introduce a cycle.
        On ValueError the graph is left exactly as it was before the call.
        """
        # Snapshot: old formula deps (edges where name is the target)
        old_edges = list(self._g.in_edges(name))

        # Tentatively apply: remove old deps, add new deps
        self._g.remove_edges_from(old_edges)
        # Ensure all dep nodes exist
        for dep in deps:
            if dep not in self._g:
                self._g.add_node(dep)
        self._g.add_edges_from([(dep, name) for dep in deps])

        # Cycle check
        try:
            nx.find_cycle(self._g)
            # If we get here a cycle was detected — rollback and raise
            self._g.remove_edges_from([(dep, name) for dep in deps])
            self._g.add_edges_from(old_edges)
            raise ValueError(
                f"Setting formula for '{name}' would introduce a cycle."
            )
        except nx.exception.NetworkXNoCycle:
            # No cycle — changes are committed
            pass

    def remove_formula_edges(self, name):
        """
        Remove all incoming edges for *name* (i.e. its formula dependencies).
        Used when a cell is redefined from formula to constant value.
        Outgoing edges (downstream dependents) are preserved.
        """
        old_edges = list(self._g.in_edges(name))
        self._g.remove_edges_from(old_edges)

    def get_transitive_dependents(self, name):
        """
        Return the set of all cells that (transitively) depend on *name*.

        With edges dep -> cell, nx.descendants follows directed edges forward,
        returning all cells reachable from *name* — exactly the transitive
        dependents.
        """
        if name not in self._g:
            return set()
        return nx.descendants(self._g, name)
