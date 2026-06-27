"""sheet.py — Sheet facade: the sole public interface for the spreadsheet engine."""

import networkx as nx

from dag import DependencyGraph
from evaluator import evaluate, extract_refs


class Sheet:
    def __init__(self) -> None:
        # Stores literal values (and cached formula results after recalc).
        self._values: dict = {}
        # Stores raw formula strings for formula cells only.
        self._formulas: dict = {}
        self._dag: DependencyGraph = DependencyGraph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, cell: str, number: float) -> None:
        """Store a literal numeric value in a cell.

        Clears any formula previously stored in the cell and removes its
        dependency edges.
        """
        self._values[cell] = float(number)
        # Remove formula if this cell previously held one.
        self._formulas.pop(cell, None)
        # Clear dependencies: cell no longer depends on anything.
        # set_dependencies with empty list removes all dep->cell edges.
        self._dag.set_dependencies(cell, [])

    def set_formula(self, cell: str, expr: str) -> None:
        """Store a formula for a cell and update the dependency graph.

        Does NOT immediately evaluate the formula.
        """
        self._formulas[cell] = expr
        # Ensure the cell node exists in the DAG.
        self._dag.add_cell(cell)
        # Extract referenced cells and register dependencies.
        refs = extract_refs(expr)
        self._dag.set_dependencies(cell, refs)
        # Ensure referenced cells that don't exist yet have nodes in the DAG.
        for ref in refs:
            self._dag.add_cell(ref)

    def get_value(self, cell: str) -> float:
        """Return the current value of a cell.

        For literal cells: returns the stored number (0.0 if never set).
        For formula cells: evaluates using current values of all dependencies,
        in correct topological order.
        Raises ValueError if a cycle is detected.
        """
        if cell not in self._formulas:
            return float(self._values.get(cell, 0.0))

        # Cycle check before attempting evaluation.
        if self._dag.has_cycle():
            raise ValueError("Cycle detected in dependency graph")

        # Compute the transitive dependency set for this cell.
        # With dep->cell edges, nx.ancestors gives all nodes that can reach
        # `cell` by following directed edges — i.e., all transitive deps.
        g = self._dag.graph
        dep_set = nx.ancestors(g, cell)  # set of cell addresses
        dep_set.add(cell)

        # Evaluate in topological order, but only for cells in dep_set.
        topo = self._dag.topological_order()  # raises ValueError on cycle
        local_values: dict = {}

        for c in topo:
            if c not in dep_set:
                continue
            if c in self._formulas:
                # Build a lookup that prefers locally-computed values,
                # falling back to stored values, then 0.0.
                lookup = _make_lookup(local_values, self._values)
                local_values[c] = evaluate(self._formulas[c], lookup)
            else:
                local_values[c] = float(self._values.get(c, 0.0))

        return float(local_values.get(cell, 0.0))

    def recalc(self) -> None:
        """Re-evaluate all formula cells in topological order.

        Raises ValueError if the dependency graph contains a cycle.
        """
        if self._dag.has_cycle():
            raise ValueError("Cycle detected in dependency graph")

        topo = self._dag.topological_order()  # raises ValueError on cycle

        for cell in topo:
            if cell in self._formulas:
                lookup = _make_lookup(self._values, {})
                self._values[cell] = evaluate(self._formulas[cell], lookup)

    def cells_in_topological_order(self) -> list:
        """Return all registered cells in topological order (deps first).

        Raises ValueError if the dependency graph contains a cycle.
        """
        return self._dag.topological_order()

    def detect_cycle(self) -> bool:
        """Return True if the dependency graph contains a cycle, False otherwise.

        Never raises; safe to call even on cyclic graphs.
        """
        return self._dag.has_cycle()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_lookup(primary: dict, secondary: dict) -> dict:
    """Return a combined read-only view: primary overrides secondary.

    Missing keys in both sources default to 0.0 at evaluation time
    (handled inside evaluate()).
    """
    merged = dict(secondary)
    merged.update(primary)
    return merged
