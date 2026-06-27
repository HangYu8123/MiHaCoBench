"""
sheet.py — Public Sheet facade.
"""

import re

from parser import parse_formula
from evaluator import evaluate


_REF_RE = re.compile(r"^[A-Z]+\d+$")
_NUM_RE = re.compile(r"^-?(?:\d+\.?\d*|\.\d+)$")


class Sheet:
    """
    Mini spreadsheet engine.

    Cells hold one of:
      - A float (parsed from a bare number string)
      - A str   (arbitrary text not starting with '=')
      - A formula (str starting with '='); evaluated lazily.
    """

    def __init__(self):
        # Maps ref -> raw content string
        self._raw: dict[str, str] = {}
        # Cache of evaluated values; invalidated on set_cell / recalculate
        self._cache: dict[str, float | str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_cell(self, ref: str, content: str) -> None:
        if not _REF_RE.match(ref):
            raise ValueError(f"Invalid cell reference: {ref!r}")
        self._raw[ref] = content
        # Invalidate the whole cache so dependents are re-evaluated
        self._cache.clear()

    def get_value(self, ref: str) -> float | str:
        if ref in self._cache:
            return self._cache[ref]
        result = self._eval_cell(ref, set())
        self._cache[ref] = result
        return result

    def recalculate(self) -> None:
        """Force re-evaluation of all formula cells."""
        self._cache.clear()
        for ref in list(self._raw.keys()):
            self._cache[ref] = self._eval_cell(ref, set())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _eval_cell(self, ref: str, visiting: set) -> float | str:
        """
        Evaluate a single cell, respecting the *visiting* set for cycle detection.
        """
        # Unknown cells default to 0.0
        if ref not in self._raw:
            return 0.0

        content = self._raw[ref]

        # Formula
        if content.startswith('='):
            if ref in visiting:
                raise ValueError(f"Circular reference detected involving {ref}")
            visiting = visiting | {ref}   # immutable update; don't modify caller's set
            ast = parse_formula(content[1:])
            result = evaluate(ast, self, visiting)
            return result

        # Bare number?
        if _NUM_RE.match(content):
            return float(content)

        # Plain text
        return content
