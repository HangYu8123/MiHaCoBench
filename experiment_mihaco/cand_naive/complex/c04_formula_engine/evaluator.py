"""
evaluator.py — Walks the AST and evaluates it against a Sheet.

The evaluator is given a callback `get_cell_value(ref: str) -> float | str`
and `get_range_values(range_ref: str) -> list[float | str]`.
"""

import re
import numpy as np
from typing import Callable


def _parse_cell_ref(ref: str):
    """Split 'A1' -> ('A', 1), 'AA10' -> ('AA', 10)."""
    m = re.match(r'^([A-Z]+)(\d+)$', ref)
    if not m:
        raise ValueError(f"Invalid cell reference: {ref!r}")
    return m.group(1), int(m.group(2))


def _col_to_index(col: str) -> int:
    """Convert column letters to 0-based index. 'A'->0, 'Z'->25, 'AA'->26."""
    result = 0
    for ch in col:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result - 1


def expand_range(range_ref: str):
    """
    Expand 'A1:B3' into a list of cell references.
    Returns list in row-major order.
    """
    left, right = range_ref.split(':')
    col1, row1 = _parse_cell_ref(left)
    col2, row2 = _parse_cell_ref(right)

    c1 = _col_to_index(col1)
    c2 = _col_to_index(col2)
    r1, r2 = min(row1, row2), max(row1, row2)
    ca, cb = min(c1, c2), max(c1, c2)

    refs = []
    for r in range(r1, r2 + 1):
        for c in range(ca, cb + 1):
            col_str = _index_to_col(c)
            refs.append(f"{col_str}{r}")
    return refs


def _index_to_col(idx: int) -> str:
    """Convert 0-based column index to letters. 0->'A', 25->'Z', 26->'AA'."""
    result = []
    idx += 1  # 1-based
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        result.append(chr(ord('A') + rem))
    return ''.join(reversed(result))


class Evaluator:
    def __init__(self,
                 get_cell: Callable[[str], 'float | str'],
                 current_path: 'set[str] | None' = None):
        """
        get_cell: callable(ref) -> float | str, handles cycle detection externally
        current_path: set of cell refs currently being evaluated (for cycle detection)
        """
        self._get_cell = get_cell
        self._path = current_path if current_path is not None else set()

    def eval(self, node: dict) -> 'float | str':
        t = node['type']
        if t == 'number':
            return float(node['value'])
        if t == 'string':
            return node['value']
        if t == 'cell_ref':
            return self._get_cell(node['ref'])
        if t == 'range':
            raise ValueError("Range used outside of function context")
        if t == 'binop':
            return self._eval_binop(node)
        if t == 'func':
            return self._eval_func(node)
        if t == 'if':
            return self._eval_if(node)
        raise ValueError(f"Unknown AST node type: {t!r}")

    def _eval_binop(self, node: dict) -> float:
        op = node['op']
        left = self.eval(node['left'])
        right = self.eval(node['right'])
        # Coerce to float for arithmetic
        try:
            l = float(left)
            r = float(right)
        except (TypeError, ValueError):
            raise ValueError(f"Non-numeric operands for {op!r}: {left!r}, {right!r}")
        if op == '+':
            return l + r
        if op == '-':
            return l - r
        if op == '*':
            return l * r
        if op == '/':
            if r == 0:
                raise ZeroDivisionError("Division by zero")
            return l / r
        if op == '^':
            return float(l ** r)
        raise ValueError(f"Unknown operator: {op!r}")

    def _get_range_values(self, range_ref: str) -> list:
        refs = expand_range(range_ref)
        values = []
        for ref in refs:
            v = self._get_cell(ref)
            values.append(v)
        return values

    def _to_numeric(self, values: list, skip_non_numeric: bool = True) -> np.ndarray:
        """Convert list of values to numpy array, skipping non-numeric if requested."""
        nums = []
        for v in values:
            try:
                nums.append(float(v))
            except (TypeError, ValueError):
                if not skip_non_numeric:
                    nums.append(0.0)
        return np.array(nums, dtype=float)

    def _eval_func(self, node: dict) -> float:
        name = node['name']
        args = node['args']

        # Collect all numeric values from args (ranges or expressions)
        values = []
        for arg in args:
            if arg['type'] == 'range':
                values.extend(self._get_range_values(arg['ref']))
            else:
                v = self.eval(arg)
                values.append(v)

        arr = self._to_numeric(values)

        if name == 'SUM':
            return float(np.sum(arr)) if len(arr) > 0 else 0.0
        if name == 'AVG':
            return float(np.mean(arr)) if len(arr) > 0 else 0.0
        if name == 'MIN':
            return float(np.min(arr)) if len(arr) > 0 else 0.0
        if name == 'MAX':
            return float(np.max(arr)) if len(arr) > 0 else 0.0
        raise ValueError(f"Unknown function: {name!r}")

    def _eval_if(self, node: dict) -> 'float | str':
        cond_node = node['cond']
        cond_result = self._eval_cond(cond_node)
        if cond_result:
            return self.eval(node['then'])
        else:
            return self.eval(node['else'])

    def _eval_cond(self, cond_node: dict) -> bool:
        op = cond_node['op']
        left = self.eval(cond_node['left'])
        right = self.eval(cond_node['right'])

        # Try numeric comparison first
        try:
            l = float(left)
            r = float(right)
            if op == '=':
                return l == r
            if op == '<>':
                return l != r
            if op == '<':
                return l < r
            if op == '<=':
                return l <= r
            if op == '>':
                return l > r
            if op == '>=':
                return l >= r
        except (TypeError, ValueError):
            # Fall back to string comparison
            if op == '=':
                return str(left) == str(right)
            if op == '<>':
                return str(left) != str(right)
            # Other comparisons on strings
            if op == '<':
                return str(left) < str(right)
            if op == '<=':
                return str(left) <= str(right)
            if op == '>':
                return str(left) > str(right)
            if op == '>=':
                return str(left) >= str(right)

        raise ValueError(f"Unknown comparison operator: {op!r}")


def evaluate(ast_node: dict, get_cell: Callable[[str], 'float | str'],
             current_path: 'set[str] | None' = None) -> 'float | str':
    """
    Evaluate an AST node against the given cell-value function.
    """
    ev = Evaluator(get_cell, current_path)
    return ev.eval(ast_node)
