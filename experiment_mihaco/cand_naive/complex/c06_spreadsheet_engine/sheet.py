"""
sheet.py — Facade exposing the public Sheet class.
"""

from dag import DependencyGraph
from evaluator import evaluate_formula, extract_cell_refs


class Sheet:
    """
    Mini spreadsheet engine.

    Cells can hold either literal numeric values or formulas.
    Formulas are lazily evaluated; use recalc() to propagate updates.
    """

    def __init__(self):
        self._dag = DependencyGraph()
        # Maps cell name -> float (literal or last-evaluated formula result)
        self._values: dict[str, float] = {}
        # Maps cell name -> formula string (None if the cell holds a literal)
        self._formulas: dict[str, str | None] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, cell: str, number: float) -> None:
        """Store a literal numeric value; clears any formula for this cell."""
        cell = cell.upper()
        self._values[cell] = float(number)
        self._formulas[cell] = None
        # Remove dependencies: this cell no longer depends on anything
        self._dag.ensure_node(cell)
        self._dag.set_dependencies(cell, [])

    def set_formula(self, cell: str, expr: str) -> None:
        """
        Store a formula for the cell and update the dependency graph.
        Does NOT evaluate the formula immediately.
        """
        cell = cell.upper()
        expr = expr.strip()
        if not expr.startswith("="):
            raise ValueError(f"Formula must start with '=': {expr!r}")

        self._formulas[cell] = expr

        # Extract cell references and update the DAG
        body = expr[1:]
        refs = extract_cell_refs(body)
        self._dag.ensure_node(cell)
        self._dag.set_dependencies(cell, refs)

        # Ensure all referenced cells are nodes in the graph even if not set
        for ref in refs:
            self._dag.ensure_node(ref)

    def get_value(self, cell: str) -> float:
        """
        Return the current value of the cell.
        - Literal cells: the stored float (0.0 if never set).
        - Formula cells: evaluates the formula on demand.
        Raises ValueError if a cycle is detected.
        """
        cell = cell.upper()

        if self._dag.has_cycle():
            raise ValueError(
                f"Cannot get value for '{cell}': dependency graph contains a cycle."
            )

        formula = self._formulas.get(cell)
        if formula is not None:
            return evaluate_formula(formula, self._cell_lookup)

        return self._values.get(cell, 0.0)

    def recalc(self) -> None:
        """
        Re-evaluate all formula cells in topological order.
        Raises ValueError if a cycle exists.
        """
        order = self.cells_in_topological_order()  # raises ValueError on cycle
        for cell in order:
            formula = self._formulas.get(cell)
            if formula is not None:
                self._values[cell] = evaluate_formula(formula, self._cell_lookup_cached)

    def cells_in_topological_order(self) -> list[str]:
        """
        Return all known cells in topological order (dependencies first).
        Raises ValueError if a cycle exists.
        """
        return self._dag.topological_order()

    def detect_cycle(self) -> bool:
        """Return True if the dependency graph contains a cycle; never raises."""
        return self._dag.has_cycle()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cell_lookup(self, cell_name: str) -> float:
        """
        Recursively evaluate a cell's value for on-demand get_value().
        Assumes cycle check has already been done by the caller.
        """
        cell_name = cell_name.upper()
        formula = self._formulas.get(cell_name)
        if formula is not None:
            return evaluate_formula(formula, self._cell_lookup)
        return self._values.get(cell_name, 0.0)

    def _cell_lookup_cached(self, cell_name: str) -> float:
        """
        Look up a cell's value during recalc().
        By this point cells have already been evaluated in topological order,
        so self._values holds the up-to-date result.
        """
        cell_name = cell_name.upper()
        return self._values.get(cell_name, 0.0)
