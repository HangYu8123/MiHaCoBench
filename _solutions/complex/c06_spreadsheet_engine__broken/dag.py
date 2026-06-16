"""dag.py — Dependency graph for the spreadsheet engine.

Uses networkx to track which cells depend on which cells,
providing topological ordering and cycle detection.
"""
from __future__ import annotations

from typing import List

import networkx as nx


class DependencyGraph:
    """Tracks cell dependency relationships using a networkx DiGraph.

    An edge (u -> v) means: cell v depends on cell u (u must be evaluated
    before v). Equivalently, when u changes, v must be recalculated.
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    def add_cell(self, cell: str) -> None:
        """Ensure a cell node exists in the graph."""
        self._graph.add_node(cell)

    def set_dependencies(self, cell: str, deps: List[str]) -> None:
        """Set the cells that *cell* depends on.

        Removes all old incoming edges for *cell* (from previous set_formula
        calls) and adds new ones. Each dep d adds an edge d -> cell meaning
        'cell depends on d'.
        """
        # Remove old dependency edges into this cell
        old_preds = list(self._graph.predecessors(cell))
        for pred in old_preds:
            self._graph.remove_edge(pred, cell)

        # Add new dependency edges
        for dep in deps:
            self._graph.add_node(dep)
            self._graph.add_edge(dep, cell)

        # Make sure cell itself is in the graph
        self._graph.add_node(cell)

    def clear_dependencies(self, cell: str) -> None:
        """Remove all dependency edges coming into *cell* (used when set_value replaces formula)."""
        old_preds = list(self._graph.predecessors(cell))
        for pred in old_preds:
            self._graph.remove_edge(pred, cell)

    def has_cycle(self) -> bool:
        """Return True if the dependency graph contains a cycle."""
        return not nx.is_directed_acyclic_graph(self._graph)

    def topological_order(self) -> List[str]:
        """Return all cell names in topological order (dependencies before dependents).

        Raises ValueError if a cycle exists.
        """
        if self.has_cycle():
            raise ValueError("Cyclic dependency detected in spreadsheet")
        return list(nx.topological_sort(self._graph))

    def dependents_of(self, cell: str) -> List[str]:
        """Return all cells that directly or transitively depend on *cell*,
        in topological order (so we can re-evaluate them in correct sequence).
        """
        if cell not in self._graph:
            return []
        descendants = nx.descendants(self._graph, cell)
        sub = self._graph.subgraph(descendants)
        if not nx.is_directed_acyclic_graph(sub):
            raise ValueError("Cyclic dependency detected in spreadsheet")
        return list(nx.topological_sort(sub))

    def all_cells(self) -> List[str]:
        """Return all cell names known to the graph."""
        return list(self._graph.nodes())
