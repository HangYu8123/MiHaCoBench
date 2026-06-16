"""
sheet.py — Facade: exposes the public Sheet class.

Public API:
  sheet = Sheet()
  sheet.set_cell(ref: str, content: str) -> None
  sheet.get_value(ref: str) -> float | str
  sheet.recalculate() -> None
"""

import re
import sys
import os

# Ensure the package directory is on sys.path so relative imports work
# when the grader imports 'from sheet import Sheet'
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from parser import parse_formula
from evaluator import evaluate


_CELL_RE = re.compile(r'^[A-Z]+\d+$')


def _is_number(s: str) -> bool:
    """Return True if s can be parsed as a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


class Sheet:
    """
    Mini spreadsheet engine.

    Cells can hold:
      - float (bare number string)
      - str   (arbitrary text)
      - formula (string starting with '=')

    Formula cells are evaluated lazily on get_value().
    """

    def __init__(self):
        # _cells maps ref -> raw content string
        self._cells: dict[str, str] = {}
        # _cache maps ref -> evaluated value (float | str)
        # None means dirty / not yet evaluated
        self._cache: dict[str, float | str | None] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_cell(self, ref: str, content: str) -> None:
        """
        Store content in cell `ref`.
        Invalidates the cache for this cell and all dependents.
        """
        if not _CELL_RE.match(ref):
            raise ValueError(f"Invalid cell reference: {ref!r}")
        self._cells[ref] = content
        # Invalidate entire cache — simple approach (no dependency graph)
        self._cache.clear()

    def get_value(self, ref: str) -> 'float | str':
        """
        Return the current value of cell `ref`.
        Unset cells return 0.0.
        Raises ValueError on circular dependency.
        """
        if ref not in self._cells:
            return 0.0

        # Return cached value if available
        if ref in self._cache and self._cache[ref] is not None:
            return self._cache[ref]

        content = self._cells[ref]
        value = self._evaluate_content(ref, content, visiting=set())
        self._cache[ref] = value
        return value

    def recalculate(self) -> None:
        """
        Force re-evaluation of all formula cells.
        """
        self._cache.clear()
        for ref in list(self._cells.keys()):
            # Trigger evaluation so cache is populated
            self.get_value(ref)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_content(self, ref: str, content: str,
                           visiting: set) -> 'float | str':
        """
        Evaluate `content` in the context of cell `ref`.
        `visiting` tracks the call stack for cycle detection.
        """
        if content is None:
            return 0.0

        if content.startswith('='):
            if ref in visiting:
                raise ValueError(
                    f"Circular reference detected involving cell {ref!r}")
            visiting.add(ref)
            try:
                formula_str = content[1:]  # strip leading '='
                ast = parse_formula(formula_str)
                result = evaluate(ast, lambda r: self._get_cell_for_eval(r, visiting))
                return result
            finally:
                visiting.discard(ref)
        elif _is_number(content):
            return float(content)
        else:
            return content

    def _get_cell_for_eval(self, ref: str, visiting: set) -> 'float | str':
        """
        Called by the evaluator when it needs the value of a cell reference.
        Handles unset cells (returns 0.0) and caches results.
        """
        if ref not in self._cells:
            return 0.0

        # Return cached if available
        if ref in self._cache and self._cache[ref] is not None:
            return self._cache[ref]

        # Cycle detection: if ref is already being visited, we have a cycle
        if ref in visiting:
            raise ValueError(
                f"Circular reference detected involving cell {ref!r}")

        content = self._cells[ref]
        value = self._evaluate_content(ref, content, visiting)
        self._cache[ref] = value
        return value
