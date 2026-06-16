"""
graph.py — Dependency graph wrapper using networkx DiGraph.

Edge direction: dep -> name
  meaning: "dep is a dependency of name" / "name depends on dep"
  so descendants(G, changed_node) gives all nodes that depend on changed_node.
"""

import networkx as nx


class Graph:
    """Wraps a networkx DiGraph for dependency tracking."""

    def __init__(self):
        self._g = nx.DiGraph()

    def ensure_node(self, name):
        """Ensure a node exists in the graph."""
        if name not in self._g:
            self._g.add_node(name)

    def remove_outgoing_edges(self, name):
        """
        Remove all outgoing edges FROM name.
        Since edges go dep -> dependent, outgoing edges from `name` mean
        `name` is a dependency of something.
        But here we use this to remove edges where `name` is the dependent,
        i.e., remove all edges where `name` is the *target*.

        Wait — we need to be careful about direction:
        - Edge direction: dep -> name (dep points to its dependent)
        - So if `name` is a formula cell with deps [d1, d2],
          there are edges d1 -> name and d2 -> name (incoming edges to name)
        - We want to remove edges that represent `name`'s dependencies
          i.e., remove all incoming edges to `name`
        """
        # Remove all incoming edges to `name` (its dependencies)
        predecessors = list(self._g.predecessors(name))
        for pred in predecessors:
            self._g.remove_edge(pred, name)

    def add_dependency_edges(self, name, deps):
        """
        Add edges dep -> name for each dep in deps.
        This means `name` depends on `dep`.
        """
        for dep in deps:
            self.ensure_node(dep)
            self._g.add_edge(dep, name)

    def get_descendants(self, name):
        """
        Return all transitive dependents of `name`.
        These are nodes reachable from `name` following directed edges
        (dep -> dependent direction), so descendants are all cells
        that (directly or transitively) depend on `name`.
        """
        if name not in self._g:
            return set()
        return nx.descendants(self._g, name)

    def would_create_cycle(self, name, deps):
        """
        Check if adding edges dep -> name for each dep would create a cycle.
        Returns True if a cycle would be created.
        Uses a copy of the graph to avoid mutation.
        """
        g_copy = self._g.copy()
        # Ensure the name node exists
        if name not in g_copy:
            g_copy.add_node(name)
        # Add the new edges
        for dep in deps:
            if dep not in g_copy:
                g_copy.add_node(dep)
            g_copy.add_edge(dep, name)
        # Check if still a DAG
        return not nx.is_directed_acyclic_graph(g_copy)

    def copy_graph_state(self):
        """Return a copy of the current graph for snapshot/restore."""
        return self._g.copy()

    def restore_graph_state(self, snapshot):
        """Restore graph to a previously saved snapshot."""
        self._g = snapshot
