"""AST walker that evaluates a parsed formula against a Sheet context."""

import re
import operator as _op_module
from typing import Any, List

import numpy as np

from parser import (
    Num, Str, CellRef, Range, BinOp, FuncCall, IfExpr,
)


# ---------------------------------------------------------------------------
# Column letter <-> number helpers (1-indexed)
# ---------------------------------------------------------------------------

def _col_to_num(s: str) -> int:
    """Convert column letter(s) to a 1-based integer (A=1, Z=26, AA=27, ...)."""
    result = 0
    for ch in s:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result


def _num_to_col(n: int) -> str:
    """Convert 1-based integer back to column letter(s)."""
    s = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(ord('A') + rem) + s
    return s


def _expand_range(start: str, end: str) -> List[str]:
    """Expand a range like 'A1:B3' into a list of cell references."""
    m1 = re.fullmatch(r'([A-Z]+)(\d+)', start)
    m2 = re.fullmatch(r'([A-Z]+)(\d+)', end)
    if not m1 or not m2:
        raise ValueError(f"Invalid range endpoints: {start!r} {end!r}")

    col1 = _col_to_num(m1.group(1))
    row1 = int(m1.group(2))
    col2 = _col_to_num(m2.group(1))
    row2 = int(m2.group(2))

    # Normalise so col1 <= col2 and row1 <= row2
    if col1 > col2:
        col1, col2 = col2, col1
    if row1 > row2:
        row1, row2 = row2, row1

    refs: List[str] = []
    for col in range(col1, col2 + 1):
        for row in range(row1, row2 + 1):
            refs.append(f'{_num_to_col(col)}{row}')
    return refs


# ---------------------------------------------------------------------------
# Comparison operator dispatch
# ---------------------------------------------------------------------------

_CMP_OPS = {
    '=':  _op_module.eq,
    '<>': _op_module.ne,
    '<':  _op_module.lt,
    '<=': _op_module.le,
    '>':  _op_module.gt,
    '>=': _op_module.ge,
}


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------

def evaluate(node: Any, sheet: Any) -> Any:
    """Recursively evaluate an AST node against a Sheet."""

    if isinstance(node, Num):
        return float(node.val)

    if isinstance(node, Str):
        return node.val

    if isinstance(node, CellRef):
        return sheet.get_value(node.ref)

    if isinstance(node, Range):
        # A bare Range node should not appear outside of function calls;
        # return its expansion as a list (only reachable from FuncCall).
        return _expand_range(node.start, node.end)

    if isinstance(node, BinOp):
        left = evaluate(node.left, sheet)
        right = evaluate(node.right, sheet)
        op = node.op
        # Coerce to float for arithmetic
        left_f = float(left) if isinstance(left, (int, float)) else float(left)
        right_f = float(right) if isinstance(right, (int, float)) else float(right)
        if op == '+':
            return left_f + right_f
        if op == '-':
            return left_f - right_f
        if op == '*':
            return left_f * right_f
        if op == '/':
            return left_f / right_f
        if op == '^':
            return left_f ** right_f
        raise ValueError(f"Unknown operator: {op!r}")

    if isinstance(node, IfExpr):
        left_val = evaluate(node.left, sheet)
        right_val = evaluate(node.right, sheet)
        cmp_fn = _CMP_OPS.get(node.cond_op)
        if cmp_fn is None:
            raise ValueError(f"Unknown comparison operator: {node.cond_op!r}")
        # Compare numerically if both sides are numeric, else compare as values
        try:
            condition = cmp_fn(float(left_val), float(right_val))
        except (TypeError, ValueError):
            condition = cmp_fn(left_val, right_val)
        return evaluate(node.true_val, sheet) if condition else evaluate(node.false_val, sheet)

    if isinstance(node, FuncCall):
        return _eval_func(node, sheet)

    raise TypeError(f"Unknown AST node type: {type(node).__name__}")


# ---------------------------------------------------------------------------
# Function evaluation
# ---------------------------------------------------------------------------

def _collect_values(args: List[Any], sheet: Any) -> List[float]:
    """Collect all numeric values from function arguments (ranges expand)."""
    numeric: List[float] = []
    for arg in args:
        if isinstance(arg, Range):
            refs = _expand_range(arg.start, arg.end)
            for ref in refs:
                v = sheet.get_value(ref)
                try:
                    numeric.append(float(v))
                except (TypeError, ValueError):
                    pass  # skip non-numeric cells
        else:
            v = evaluate(arg, sheet)
            try:
                numeric.append(float(v))
            except (TypeError, ValueError):
                pass  # skip non-numeric
    return numeric


def _collect_sum_values(args: List[Any], sheet: Any) -> List[float]:
    """Collect values for SUM/AVG — non-numeric cells treated as 0.0."""
    values: List[float] = []
    for arg in args:
        if isinstance(arg, Range):
            refs = _expand_range(arg.start, arg.end)
            for ref in refs:
                v = sheet.get_value(ref)
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    values.append(0.0)
        else:
            v = evaluate(arg, sheet)
            try:
                values.append(float(v))
            except (TypeError, ValueError):
                values.append(0.0)
    return values


def _eval_func(node: FuncCall, sheet: Any) -> Any:
    name = node.name
    args = node.args

    if name == 'SUM':
        values = _collect_sum_values(args, sheet)
        if not values:
            return 0.0
        return float(np.sum(np.array(values, dtype=float)))

    if name == 'AVG':
        # Per spec: non-numeric cells in a range are "skipped" for AVG
        # so we filter them out before computing the mean.
        numeric: List[float] = []
        for arg in args:
            if isinstance(arg, Range):
                refs = _expand_range(arg.start, arg.end)
                for ref in refs:
                    v = sheet.get_value(ref)
                    try:
                        numeric.append(float(v))
                    except (TypeError, ValueError):
                        pass  # skip
            else:
                v = evaluate(arg, sheet)
                try:
                    numeric.append(float(v))
                except (TypeError, ValueError):
                    pass
        if not numeric:
            return 0.0
        return float(np.mean(np.array(numeric, dtype=float)))

    if name == 'MIN':
        values = _collect_values(args, sheet)
        if not values:
            return 0.0
        return float(np.min(np.array(values, dtype=float)))

    if name == 'MAX':
        values = _collect_values(args, sheet)
        if not values:
            return 0.0
        return float(np.max(np.array(values, dtype=float)))

    raise ValueError(f"Unknown function: {name!r}")
