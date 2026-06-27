"""
sheet.py — Sheet facade: the sole public interface for the spreadsheet engine.

Imports
-------
from sheet import Sheet

The Sheet class coordinates:
  - dag.DependencyGraph  for tracking cell dependencies
  - evaluator            for formula tokenization and evaluation
"""
from dag import DependencyGraph
from evaluator import extract_cell_refs, evaluate


class Sheet:
    def __init__(self):
        self._values: dict = {}    # cell -> float (literal values)
        self._formulas: dict = {}  # cell -> str   (formula strings, e.g. "=A1+B1")
        self._dag = DependencyGraph()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def set_value(self, cell: str, number: float) -> None:
        """Store a literal value in cell; clear any formula previously there."""
        self._values[cell] = float(number)
        # Remove formula if one existed
        self._formulas.pop(cell, None)
        # Register in DAG and clear all dependencies (it's now a literal)
        self._dag.add_cell(cell)
        self._dag.set_dependencies(cell, [])

    def set_formula(self, cell: str, expr: str) -> None:
        """
        Store a formula in cell and update the dependency graph.

        Does NOT immediately evaluate the formula.
        """
        self._formulas[cell] = expr
        # Remove any cached literal value so get_value uses the formula
        self._values.pop(cell, None)
        # Register cell in DAG
        self._dag.add_cell(cell)
        # Extract referenced cells and update dependencies
        deps = extract_cell_refs(expr)
        self._dag.set_dependencies(cell, deps)

    def get_value(self, cell: str) -> float:
        """
        Return the current value of cell as a float.

        - For formula cells: evaluates the formula live using current values
          of all referenced cells (recursive live evaluation, not cached).
        - For literal cells: returns the stored number.
        - Unset cells: return 0.0.
        - Raises ValueError if a cycle exists in the dependency graph.
        """
        if self._dag.has_cycle():
            raise ValueError("Cycle detected in dependency graph")

        if cell in self._formulas:
            # Evaluate the formula live; referenced cells are resolved
            # via recursive get_value calls (deps-first order is guaranteed
            # by the DAG being acyclic — no cycle was raised above).
            def lookup(ref: str) -> float:
                return self.get_value(ref)
            return evaluate(self._formulas[cell], lookup)

        return float(self._values.get(cell, 0.0))

    def recalc(self) -> None:
        """
        Re-evaluate all formula cells in topological order and cache results.

        Raises ValueError if any cycle exists.
        """
        order = self._dag.topological_order()  # raises ValueError on cycle
        for cell in order:
            if cell in self._formulas:
                def lookup(ref: str, _order=order) -> float:
                    return self._values.get(ref, 0.0)
                result = evaluate(self._formulas[cell], lookup)
                self._values[cell] = result

    def cells_in_topological_order(self) -> list:
        """
        Return all set cells in topological order (dependencies before dependents).

        Raises ValueError if a cycle exists.
        """
        topo = self._dag.topological_order()  # raises ValueError on cycle
        # Filter to only cells that have been set (literal or formula)
        set_cells = set(self._values.keys()) | set(self._formulas.keys())
        return [c for c in topo if c in set_cells]

    def detect_cycle(self) -> bool:
        """Return True if the dependency graph contains a cycle; does not raise."""
        return self._dag.has_cycle()
