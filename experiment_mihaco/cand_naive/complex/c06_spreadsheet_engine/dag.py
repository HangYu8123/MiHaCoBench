"""
dag.py — Dependency graph for the mini spreadsheet engine.
Uses networkx for the DAG and topological sort.
"""

import networkx as nx


class DependencyGraph:
    """
    Tracks cell dependencies using a directed graph.
    An edge A -> B means "B depends on A" (A is a predecessor of B).
    """

    def __init__(self):
        self._graph = nx.DiGraph()

    def ensure_node(self, cell: str) -> None:
        """Add a node for the cell if not already present."""
        if not self._graph.has_node(cell):
            self._graph.add_node(cell)

    def set_dependencies(self, cell: str, deps: list[str]) -> None:
        """
        Declare that `cell` depends on the cells listed in `deps`.
        Replaces any previous dependency edges for this cell.
        """
        self.ensure_node(cell)

        # Remove all existing incoming edges to this cell (old dependencies)
        old_preds = list(self._graph.predecessors(cell))
        for pred in old_preds:
            self._graph.remove_edge(pred, cell)

        # Add new dependency edges: dep -> cell
        for dep in deps:
            self.ensure_node(dep)
            self._graph.add_edge(dep, cell)

    def has_cycle(self) -> bool:
        """Return True if the graph contains a cycle."""
        return not nx.is_directed_acyclic_graph(self._graph)

    def topological_order(self) -> list[str]:
        """
        Return all nodes in topological order (dependencies before dependents).
        Raises ValueError if a cycle exists.
        """
        if self.has_cycle():
            raise ValueError("Dependency graph contains a cycle.")
        return list(nx.topological_sort(self._graph))

    def nodes(self) -> list[str]:
        """Return the list of all nodes in the graph."""
        return list(self._graph.nodes())
