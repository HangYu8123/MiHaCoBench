"""
dag.py — DependencyGraph class using networkx.

Edge convention: dep → cell  (dep "feeds" cell).
This means nx.topological_sort yields dependencies before their dependents,
which is exactly the order needed for recalc().
"""
import networkx as nx


class DependencyGraph:
    def __init__(self):
        self._graph = nx.DiGraph()

    def add_cell(self, cell: str) -> None:
        """Add a node for cell if not already present."""
        if cell not in self._graph:
            self._graph.add_node(cell)

    def set_dependencies(self, cell: str, deps: list) -> None:
        """
        Record that `cell` depends on each cell in `deps`.

        Edge direction: dep → cell  (dep feeds cell).
        Clears all prior in-edges to `cell` first, then adds dep → cell
        for each dep in deps.
        """
        # Ensure the cell node exists
        self.add_cell(cell)
        # Remove all previous in-edges (prior dependencies) to cell
        in_edges = list(self._graph.in_edges(cell))
        self._graph.remove_edges_from(in_edges)
        # Add new dep → cell edges
        for dep in deps:
            self.add_cell(dep)
            self._graph.add_edge(dep, cell)

    def topological_order(self) -> list:
        """
        Return all nodes in topological order (dependencies before dependents).

        Raises ValueError if a cycle is detected.
        """
        if not nx.is_directed_acyclic_graph(self._graph):
            raise ValueError("Cycle detected in dependency graph")
        return list(nx.topological_sort(self._graph))

    def has_cycle(self) -> bool:
        """Return True if the graph contains a cycle."""
        return not nx.is_directed_acyclic_graph(self._graph)

    def all_nodes(self) -> list:
        """Return all nodes in the graph."""
        return list(self._graph.nodes())
