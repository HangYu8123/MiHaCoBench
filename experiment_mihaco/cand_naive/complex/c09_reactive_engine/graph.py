"""
graph.py — Dependency graph tracking using networkx DiGraph.

Edges represent: dep -> dependent (i.e., if A depends on B, edge B -> A exists).
This means `descendants(graph, x)` gives all cells that depend on x (transitively).
"""

import networkx as nx


class DependencyGraph:
    """
    Wraps a networkx DiGraph where an edge A -> B means:
    "B depends on A", i.e., B's formula uses A's value.

    So networkx.descendants(graph, x) gives us all cells that (transitively) depend on x.
    """

    def __init__(self):
        self._graph = nx.DiGraph()

    def add_node(self, name):
        """Ensure a node exists in the graph."""
        if name not in self._graph:
            self._graph.add_node(name)

    def set_dependencies(self, name, deps):
        """
        Set the dependencies of `name` to `deps`.
        Removes old dependency edges, adds new ones.
        Raises ValueError if this would create a cycle.
        Returns the set of all transitive dependents of `name` (for invalidation).
        """
        # Snapshot old in-edges (predecessors of name)
        old_deps = list(self._graph.predecessors(name))

        # Remove old dependency edges
        for old_dep in old_deps:
            self._graph.remove_edge(old_dep, name)

        # Add new dependency edges
        for dep in deps:
            self.add_node(dep)
            self._graph.add_edge(dep, name)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self._graph):
            # Rollback: remove new edges, restore old ones
            for dep in deps:
                if self._graph.has_edge(dep, name):
                    self._graph.remove_edge(dep, name)
            for old_dep in old_deps:
                self._graph.add_edge(old_dep, name)
            raise ValueError(
                f"Setting formula for '{name}' with deps {deps} would create a cycle."
            )

    def get_transitive_dependents(self, name):
        """
        Return the set of all cells that transitively depend on `name`.
        Uses networkx.descendants which follows edges A->B (B depends on A).
        """
        if name not in self._graph:
            return set()
        return nx.descendants(self._graph, name)

    def topological_order(self):
        """
        Return nodes in topological order (dependency before dependent).
        """
        return list(nx.topological_sort(self._graph))

    def remove_dependencies(self, name):
        """Remove all incoming edges (dependency edges) for `name`."""
        old_deps = list(self._graph.predecessors(name))
        for dep in old_deps:
            self._graph.remove_edge(dep, name)
