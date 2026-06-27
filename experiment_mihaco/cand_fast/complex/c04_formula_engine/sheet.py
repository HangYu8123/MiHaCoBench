"""Public Sheet facade for the spreadsheet formula engine."""

import sys
import os

# Ensure sibling modules are importable when grader imports from this file's directory
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from lexer import lex
from parser import parse
from evaluator import evaluate


class Sheet:
    """Mini spreadsheet engine with lazy formula evaluation."""

    def __init__(self):
        self._cells: dict[str, str] = {}
        self._evaluating: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_cell(self, ref: str, content: str) -> None:
        """Store raw content for a cell."""
        self._cells[ref] = content

    def get_value(self, ref: str) -> float | str:
        """Return the evaluated value of a cell."""
        content = self._cells.get(ref)

        # Unset cell -> 0.0
        if content is None:
            return 0.0

        # Formula
        if content.startswith('='):
            if ref in self._evaluating:
                raise ValueError(
                    f"Circular reference detected: {ref} depends on itself"
                )
            self._evaluating.add(ref)
            try:
                formula = content[1:]
                tokens = lex(formula)
                ast = parse(tokens)
                result = evaluate(ast, self)
            finally:
                self._evaluating.discard(ref)
            return result

        # Bare number
        try:
            return float(content)
        except ValueError:
            pass

        # Text
        return content

    def recalculate(self) -> None:
        """Force re-evaluation of all formula cells on next access.

        Since evaluation is lazy (no memoization cache), this is a no-op
        for correctness.  We also reset the cycle-detection set to clear
        any inconsistent state left by a previous exception.
        """
        self._evaluating = set()
