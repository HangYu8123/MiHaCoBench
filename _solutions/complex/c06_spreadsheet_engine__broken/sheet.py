"""sheet.py — Public Sheet facade for the spreadsheet engine.

This is the only file the grader imports from. It orchestrates:
  - dag.py  (DependencyGraph via networkx)
  - evaluator.py  (formula tokenizer + evaluator)

BROKEN VARIANT: get_value() caches the result of the first formula
evaluation in _values. recalc() does NOT re-evaluate formula cells
(it silently returns without doing anything). Therefore, after an
upstream literal cell is updated via set_value() and recalc() is
called, dependent formula cells still return their stale cached values.

Localized defect: set/get literal, single formula (first call),
topological order, and cycle detection still work correctly.
Only re-propagation after upstream updates (tested via recalc) is broken.
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
        # Literal values (also caches evaluated formula values - BROKEN: never cleared)
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
        # BROKEN: does NOT invalidate formula caches for cells that depend on this cell

    def set_formula(self, cell: str, expr: str) -> None:
        """Store a formula in *cell* and update the dependency graph."""
        self._formulas[cell] = expr
        # Parse out cell references and update the DAG
        refs = extract_cell_refs(expr)
        self._dag.add_cell(cell)
        self._dag.set_dependencies(cell, refs)
        # Ensure all referenced cells are in the DAG
        for ref in refs:
            self._dag.add_cell(ref)
        # Invalidate the cached value for this cell on set_formula (correct)
        self._values.pop(cell, None)

    def get_value(self, cell: str) -> float:
        """Return the current value of *cell* as a float.

        BROKEN: Caches formula evaluation result permanently. After an upstream
        cell changes, the cached value is never invalidated, so stale results
        are returned without recalc having any effect.
        """
        if self._dag.has_cycle():
            raise ValueError(f"Cyclic dependency detected when evaluating cell {cell!r}")

        formula = self._formulas.get(cell)
        if formula is None:
            # Literal cell (or never-set cell)
            return self._values.get(cell, 0.0)

        # BROKEN: return cached value without re-evaluating if cache exists
        if cell in self._values:
            return self._values[cell]

        # First-time evaluation: compute and cache
        result = self._evaluate_formula_cell(cell, formula, set())
        self._values[cell] = result  # cache it — never invalidated by recalc
        return result

    def recalc(self) -> None:
        """Re-evaluate all formula cells in topological order.

        BROKEN: This implementation only checks for cycles but does NOT
        actually re-evaluate formula cells. The stale cached values in
        _values are never updated.
        """
        if self._dag.has_cycle():
            raise ValueError("Cyclic dependency detected during recalc()")
        # BUG: intentionally skip re-evaluation — stale cached values persist

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
                # BROKEN: uses cached value if available (stale)
                if ref in self._values:
                    return self._values[ref]
                return self._evaluate_formula_cell(ref, ref_formula, visiting)
            return self._values.get(ref, 0.0)

        return evaluate_formula(formula, cell_value_fn)
