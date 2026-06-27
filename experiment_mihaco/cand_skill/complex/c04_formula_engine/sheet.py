"""
sheet.py — Public facade for the spreadsheet formula engine.

Exposes the Sheet class; all formula parsing and evaluation is delegated
to lexer.py, parser.py, and evaluator.py.
"""

from typing import Dict, Optional, Set, Union

from parser import parse
from evaluator import evaluate


class Sheet:
    """
    A simple spreadsheet engine.

    Cells are identified by references like "A1", "B2", "AA10".
    Content may be:
      - A bare number string ("3.5", "-1") — stored and returned as float.
      - A plain string (no '=' prefix) — stored and returned as str.
      - A formula string starting with '=' — evaluated lazily on get_value.

    Cycle detection: if evaluating a formula requires a cell that is already
    being evaluated in the current call chain, a ValueError is raised.
    """

    def __init__(self) -> None:
        # Raw cell content (exactly as passed to set_cell)
        self._cells: Dict[str, str] = {}
        # Evaluated value cache
        self._cache: Dict[str, Union[float, str]] = {}
        # Set of cell refs currently being evaluated (cycle detection)
        self._evaluating: Set[str] = set()

    def set_cell(self, ref: str, content: str) -> None:
        """
        Store content for a cell and invalidate its cached value.

        ref     : Cell address, e.g. "A1", "B2".
        content : Raw content string.
        """
        ref = ref.upper()
        self._cells[ref] = content
        # Invalidate this cell's cache so next get_value re-evaluates
        self._cache.pop(ref, None)

    def get_value(self, ref: str) -> Union[float, str]:
        """
        Return the evaluated value of a cell.

        - Unset cells return 0.0.
        - Bare numeric content is parsed to float.
        - Text content is returned as str.
        - Formula content ('=' prefix) is evaluated; result is cached.
        - Raises ValueError on circular dependency.
        """
        ref = ref.upper()

        # Unset cell → 0.0
        if ref not in self._cells:
            return 0.0

        # Return cached value if available
        if ref in self._cache:
            return self._cache[ref]

        content = self._cells[ref]

        # Bare number
        if not content.startswith('='):
            try:
                value: Union[float, str] = float(content)
            except ValueError:
                value = content
            self._cache[ref] = value
            return value

        # Formula — check for cycle
        if ref in self._evaluating:
            raise ValueError(f"Circular dependency detected at cell {ref!r}")

        self._evaluating.add(ref)
        try:
            ast = parse(content)
            result = evaluate(ast, self)
            # Normalise: ensure numeric results are float
            if isinstance(result, (int, float)):
                result = float(result)
            self._cache[ref] = result
            return result
        finally:
            self._evaluating.discard(ref)

    def recalculate(self) -> None:
        """
        Force re-evaluation of all formula cells.

        Clears the value cache, then evaluates every formula cell in
        definition order. After this call, get_value reflects the latest
        cell values.
        """
        # Clear entire cache so all formulas will be re-evaluated
        self._cache.clear()
        # Also clear evaluating set to avoid stale state
        self._evaluating.clear()

        # Trigger evaluation of every formula cell
        for ref, content in list(self._cells.items()):
            if content.startswith('='):
                self.get_value(ref)
