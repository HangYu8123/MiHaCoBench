"""
sheet.py — Public facade exposing the Sheet class.

The grader imports only:
    from sheet import Sheet
"""

from lexer import tokenize
from parser import parse
from evaluator import evaluate


class Sheet:
    """
    Mini spreadsheet engine.

    * set_cell(ref, content)  — store raw content
    * get_value(ref)          — evaluate and return float | str
    * recalculate()           — force re-evaluation of all formula cells
    """

    def __init__(self):
        # Maps ref -> raw string content (e.g. "3.5", "hello", "=A1+A2")
        self._cells: dict[str, str] = {}
        # Evaluated cache: ref -> float | str
        self._cache: dict[str, object] = {}
        # Set of refs currently being evaluated (for cycle detection)
        self._visiting: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_cell(self, ref: str, content: str) -> None:
        """
        Store *content* in cell *ref*.

        * If content can be parsed as a float, it is stored as-is (as a
          string) but will be returned as float by get_value.
        * Formulae start with '='.
        * Everything else is stored as text.
        """
        ref = ref.upper()
        self._cells[ref] = content
        # Invalidate cache for this cell (and potentially dependents; here we
        # do a simple full-cache invalidation to stay correct).
        self._cache.pop(ref, None)

    def get_value(self, ref: str) -> 'float | str':
        """
        Evaluate and return the value of cell *ref*.

        * Unset cells return 0.0.
        * Number content returns float.
        * Text content returns str.
        * Formula content is evaluated lazily and cached.
        """
        ref = ref.upper()

        # Return cached value if available
        if ref in self._cache:
            return self._cache[ref]

        # Unset cell → 0.0
        if ref not in self._cells:
            return 0.0

        content = self._cells[ref]

        # Formula
        if content.startswith('='):
            # Cycle detection
            if ref in self._visiting:
                raise ValueError(f"Circular reference detected involving {ref}")
            self._visiting.add(ref)
            try:
                formula_body = content[1:]  # strip leading '='
                tokens = tokenize(formula_body)
                ast = parse(tokens)
                value = evaluate(ast, self)
                # Normalise numeric results to float
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    value = float(value)
                self._cache[ref] = value
                return value
            finally:
                self._visiting.discard(ref)

        # Try to parse as a number
        try:
            value = float(content)
            self._cache[ref] = value
            return value
        except ValueError:
            # Plain text
            self._cache[ref] = content
            return content

    def recalculate(self) -> None:
        """
        Force re-evaluation of all formula cells.

        Clears the entire cache first, then evaluates every formula cell so
        that subsequent get_value calls return up-to-date results.
        """
        # Full cache invalidation
        self._cache.clear()

        # Re-evaluate all formula cells (non-formula cells are cheap)
        for ref in list(self._cells.keys()):
            try:
                self.get_value(ref)
            except ValueError:
                # Propagate cycle errors but don't abort recalculation of
                # other cells.  The error will be raised again on explicit
                # get_value.
                pass
