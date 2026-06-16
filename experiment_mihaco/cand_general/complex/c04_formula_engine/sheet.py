"""
sheet.py — Public Sheet class for the mini spreadsheet engine.

Usage:
  from sheet import Sheet

  s = Sheet()
  s.set_cell("A1", "2")
  s.set_cell("A2", "=A1+1")
  s.get_value("A2")  # -> 3.0
  s.recalculate()
"""

from parser import parse_formula
from evaluator import eval_node


class Sheet:
    """
    A mini spreadsheet that supports:
    - Storing raw values (numbers, text, formulas)
    - Lazy evaluation of formula cells
    - Cycle detection via a visiting set
    - recalculate() to force re-evaluation of all formula cells
    """

    def __init__(self):
        # Maps cell ref -> raw content string
        self._cells: dict[str, str] = {}

    def set_cell(self, ref: str, content: str) -> None:
        """
        Store raw content for a cell.
        ref: e.g. "A1", "B2", "AA10"
        content: number string, text string, or formula string starting with '='
        """
        self._cells[ref] = content

    def get_value(self, ref: str) -> float | str:
        """
        Return the evaluated value of a cell.
        - Numeric literals -> float
        - Text -> str
        - Formulas -> evaluated result (float or str)
        - Unset cells -> 0.0
        - Cycles -> raises ValueError
        """
        return self._get(ref, set())

    def _get(self, ref: str, visiting: set) -> float | str:
        """
        Internal recursive getter with cycle detection.

        visiting: set of cell refs currently being evaluated (on the call stack)
        """
        if ref in visiting:
            raise ValueError(f"Circular reference detected involving cell {ref!r}")

        content = self._cells.get(ref)

        if content is None:
            # Unset cell -> 0.0
            return 0.0

        if content.startswith('='):
            # Formula cell
            visiting.add(ref)
            try:
                formula = content[1:]  # strip leading '='
                ast = parse_formula(formula)
                result = eval_node(ast, self, visiting)
                return result
            finally:
                visiting.discard(ref)
        else:
            # Try to parse as a number
            try:
                return float(content)
            except (ValueError, TypeError):
                return content

    def recalculate(self) -> None:
        """
        Force re-evaluation of all formula cells.

        Since evaluation is lazy (no cache), this simply iterates over all
        formula cells and evaluates them to surface any errors eagerly.
        Subsequent get_value() calls will re-evaluate lazily but correctly.
        """
        formula_refs = [
            ref for ref, content in self._cells.items()
            if isinstance(content, str) and content.startswith('=')
        ]
        for ref in formula_refs:
            try:
                self._get(ref, set())
            except ValueError:
                # Re-raise cycle errors; other errors propagate naturally
                raise
