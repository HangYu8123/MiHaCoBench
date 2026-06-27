"""dag.py — Dependency graph for the spreadsheet engine.

Edge direction: dep -> cell (dependency points to the dependent cell).
This means topological_sort yields dependencies before dependents, which
is the correct evaluation order.
"""

import networkx as nx


class DependencyGraph:
    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    def add_cell(self, cell: str) -> None:
        """Ensure a node exists for this cell address."""
        self._g.add_node(cell)

    def set_dependencies(self, cell: str, deps: list) -> None:
        """Register that `cell` depends on each cell in `deps`.

        Removes any previously registered dependencies for `cell`, then
        adds edges dep -> cell for each dep.
        """
        # Ensure the cell node exists.
        self._g.add_node(cell)

        # Remove old inbound edges that encode this cell's dependencies.
        # With dep->cell direction, dependencies are the *predecessors* of cell.
        old_preds = list(self._g.predecessors(cell))
        for pred in old_preds:
            self._g.remove_edge(pred, cell)

        # Add new dependency edges: dep -> cell.
        for dep in deps:
            self._g.add_node(dep)
            self._g.add_edge(dep, cell)

    def topological_order(self) -> list:
        """Return all nodes in topological order (dependencies first).

        Raises ValueError if the graph contains a cycle.
        """
        try:
            return list(nx.topological_sort(self._g))
        except nx.NetworkXUnfeasible as exc:
            raise ValueError("Cycle detected in dependency graph") from exc

    def has_cycle(self) -> bool:
        """Return True if the graph contains a cycle, False otherwise."""
        return not nx.is_directed_acyclic_graph(self._g)

    # Expose the underlying graph for advanced queries in sheet.py.
    @property
    def graph(self) -> nx.DiGraph:
        return self._g
