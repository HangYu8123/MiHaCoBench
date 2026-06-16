"""sheet.py — Public Sheet facade for the spreadsheet engine.

This is the only file the grader imports from. It orchestrates:
  - dag.py  (DependencyGraph via networkx)
  - evaluator.py  (formula tokenizer + evaluator)
"""
from __future__ import annotations

from typing import Dict, List, Optional

from dag import DependencyGraph
from evaluator import evaluate_formula, extract_cell_refs


class Sheet:
    """A mini spreadsheet engine with formula evaluation and dependency tracking.

    Cells may hold either a literal float value or a formula string.
    Formulas reference other cells and support +, -, *, / with correct
    operator precedence and parentheses.
    """

    def __init__(self) -> None:
        # Literal values (also caches evaluated formula values after recalc)
        self._values: Dict[str, float] = {}
        # Raw formula strings for formula cells (None means literal cell)
        self._formulas: Dict[str, Optional[str]] = {}
        # Dependency DAG
        self._dag = DependencyGraph()

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def set_value(self, cell: str, number: float) -> None:
        """Store a literal numeric value in *cell*, clearing any formula."""
        self._values[cell] = float(number)
        self._formulas[cell] = None
        # Remove any formula dependencies this cell previously had
        self._dag.add_cell(cell)
        self._dag.clear_dependencies(cell)

    def set_formula(self, cell: str, expr: str) -> None:
        """Store a formula in *cell* and update the dependency graph.

        The formula is NOT evaluated immediately; it will be evaluated on the
        first get_value call or after recalc().
        """
        self._formulas[cell] = expr
        # Parse out cell references and update the DAG
        refs = extract_cell_refs(expr)
        self._dag.add_cell(cell)
        self._dag.set_dependencies(cell, refs)
        # Ensure all referenced cells are in the DAG
        for ref in refs:
            self._dag.add_cell(ref)
        # Invalidate the cached value for this cell
        self._values.pop(cell, None)

    def get_value(self, cell: str) -> float:
        """Return the current value of *cell* as a float.

        For literal cells: returns the stored number (0.0 if never set).
        For formula cells: evaluates the formula on-demand.
        Raises ValueError if a cycle is detected in the dependency graph.
        """
        if self._dag.has_cycle():
            raise ValueError(f"Cyclic dependency detected when evaluating cell {cell!r}")

        formula = self._formulas.get(cell)
        if formula is None:
            # Literal cell (or never-set cell)
            return self._values.get(cell, 0.0)

        # Formula cell: evaluate using current values
        return self._evaluate_formula_cell(cell, formula, set())

    def recalc(self) -> None:
        """Re-evaluate all formula cells in topological order.

        After this call, get_value on any cell reflects the latest state.
        Raises ValueError if a cycle exists.
        """
        if self._dag.has_cycle():
            raise ValueError("Cyclic dependency detected during recalc()")

        order = self._dag.topological_order()
        for cell in order:
            formula = self._formulas.get(cell)
            if formula is not None:
                val = self._evaluate_formula_cell(cell, formula, set())
                self._values[cell] = val

    def cells_in_topological_order(self) -> List[str]:
        """Return all tracked cells in topological order (dependencies first).

        Raises ValueError if a cycle exists.
        """
        return self._dag.topological_order()

    def detect_cycle(self) -> bool:
        """Return True if the dependency graph contains a cycle, False otherwise."""
        return self._dag.has_cycle()

    # ---------------------------------------------------------------------- #
    # Internal helpers
    # ---------------------------------------------------------------------- #

    def _evaluate_formula_cell(self, cell: str, formula: str, visiting: set) -> float:
        """Evaluate *formula* for *cell*, detecting cycles via *visiting* set."""
        if cell in visiting:
            raise ValueError(f"Cyclic dependency detected at cell {cell!r}")
        visiting = visiting | {cell}

        def cell_value_fn(ref: str) -> float:
            ref_formula = self._formulas.get(ref)
            if ref_formula is not None:
                return self._evaluate_formula_cell(ref, ref_formula, visiting)
            return self._values.get(ref, 0.0)

        return evaluate_formula(formula, cell_value_fn)
