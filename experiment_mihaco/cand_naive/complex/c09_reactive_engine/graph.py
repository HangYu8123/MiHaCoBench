"""
graph.py — Dependency tracking using a networkx DiGraph wrapper.

The dependency graph stores edges as: dependency -> dependent.
i.e., if cell B depends on cell A, there's an edge A -> B.
"""
import networkx as nx


class DependencyGraph:
    """
    Wraps a networkx DiGraph for tracking reactive dataflow dependencies.

    Edge direction: dep -> dependent (A -> B means "B depends on A").
    """

    def __init__(self):
        self._graph = nx.DiGraph()

    def ensure_node(self, name):
        """Ensure a node exists in the graph."""
        if name not in self._graph:
            self._graph.add_node(name)

    def set_dependencies(self, name, deps):
        """
        Set the dependencies for a cell (replacing any existing ones).
        Returns (True, set_of_old_dep_edges) on success.
        Raises ValueError if the new dependencies would introduce a cycle.

        Performs rollback on failure.
        """
        # Remember old in-edges for rollback
        old_predecessors = list(self._graph.predecessors(name)) if name in self._graph else []

        # Ensure the node exists
        self.ensure_node(name)

        # Remove all existing in-edges for this node
        edges_to_remove = [(pred, name) for pred in old_predecessors]
        self._graph.remove_edges_from(edges_to_remove)

        # Add new edges
        new_edges = []
        for dep in deps:
            self.ensure_node(dep)
            new_edges.append((dep, name))

        self._graph.add_edges_from(new_edges)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self._graph):
            # Rollback: remove new edges, restore old edges
            self._graph.remove_edges_from(new_edges)
            self._graph.add_edges_from(edges_to_remove)
            raise ValueError(
                f"Setting dependencies for '{name}' would introduce a cycle."
            )

        return old_predecessors

    def remove_dependencies(self, name):
        """Remove all incoming edges (dependencies) for a cell."""
        if name in self._graph:
            old_predecessors = list(self._graph.predecessors(name))
            edges_to_remove = [(pred, name) for pred in old_predecessors]
            self._graph.remove_edges_from(edges_to_remove)

    def get_transitive_dependents(self, name):
        """
        Return the set of all cells that transitively depend on `name`.
        Uses networkx.descendants (follows edges name -> ... -> dependents).
        """
        if name not in self._graph:
            return set()
        return nx.descendants(self._graph, name)

    def get_direct_deps(self, name):
        """Return the direct dependencies of a cell (its predecessors)."""
        if name not in self._graph:
            return []
        return list(self._graph.predecessors(name))

    def topological_order(self, names):
        """
        Return the given names sorted in topological order
        (dependencies before dependents).
        """
        # Get the subgraph induced by these names and their dependencies
        # We use topological_sort on the full graph, then filter
        try:
            topo = list(nx.topological_sort(self._graph))
        except nx.NetworkXUnfeasible:
            return list(names)

        name_set = set(names)
        return [n for n in topo if n in name_set]

    def has_node(self, name):
        return name in self._graph
