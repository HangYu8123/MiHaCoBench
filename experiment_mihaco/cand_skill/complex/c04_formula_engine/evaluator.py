"""
evaluator.py — AST walker for the spreadsheet formula engine.

Evaluates AST nodes produced by parser.py against a Sheet object.
"""

import re
from typing import Any, List

import numpy as np

from parser import (
    Literal, StrLiteral, CellRef, Range, BinOp, UnaryMinus, FuncCall, IfExpr
)


# ---------------------------------------------------------------------------
# Column / row utilities
# ---------------------------------------------------------------------------

def _col_to_idx(col: str) -> int:
    """Convert column letters to a 1-based integer (A=1, Z=26, AA=27, ...)."""
    result = 0
    for ch in col.upper():
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result


def _idx_to_col(n: int) -> str:
    """Convert 1-based integer to column letters."""
    col = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        col = chr(ord('A') + rem) + col
    return col


_REF_RE = re.compile(r'^([A-Z]+)(\d+)$')


def _parse_ref(ref: str):
    """Return (col_str, row_int) for a cell reference like 'A1'."""
    m = _REF_RE.match(ref.upper())
    if not m:
        raise ValueError(f"Invalid cell reference: {ref!r}")
    return m.group(1), int(m.group(2))


def _expand_range(start: str, end: str) -> List[str]:
    """
    Expand a range like A1:B3 to a list of cell refs in col-major order:
    A1, A2, A3, B1, B2, B3.
    """
    sc, sr = _parse_ref(start)
    ec, er = _parse_ref(end)

    sc_idx = _col_to_idx(sc)
    ec_idx = _col_to_idx(ec)
    # Normalise so start <= end in both dimensions
    c_lo, c_hi = min(sc_idx, ec_idx), max(sc_idx, ec_idx)
    r_lo, r_hi = min(sr, er), max(sr, er)

    refs = []
    for c in range(c_lo, c_hi + 1):
        col_str = _idx_to_col(c)
        for r in range(r_lo, r_hi + 1):
            refs.append(col_str + str(r))
    return refs


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def evaluate(node: Any, sheet: Any) -> Any:
    """
    Recursively evaluate an AST node.

    Parameters
    ----------
    node  : AST node from parser.py
    sheet : Sheet instance — must expose get_value(ref) and _evaluating set
    """

    if isinstance(node, Literal):
        return float(node.value)

    if isinstance(node, StrLiteral):
        return node.value

    if isinstance(node, CellRef):
        return _coerce_numeric(sheet.get_value(node.ref))

    if isinstance(node, Range):
        # Range on its own — collect all values (for use as function arg)
        return _resolve_range(node.start, node.end, sheet)

    if isinstance(node, UnaryMinus):
        val = evaluate(node.expr, sheet)
        return -float(val)

    if isinstance(node, BinOp):
        return _eval_binop(node, sheet)

    if isinstance(node, FuncCall):
        return _eval_func(node, sheet)

    if isinstance(node, IfExpr):
        return _eval_if(node, sheet)

    raise TypeError(f"Unknown AST node type: {type(node).__name__!r}")


def _coerce_numeric(val: Any) -> Any:
    """Leave floats/ints as-is; attempt to parse strings as float."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return val
    return val


def _resolve_range(start: str, end: str, sheet: Any) -> List[Any]:
    """Return list of evaluated values for cells in the range."""
    refs = _expand_range(start, end)
    return [_coerce_numeric(sheet.get_value(ref)) for ref in refs]


def _to_float_or_zero(val: Any) -> float:
    """Convert a value to float; return 0.0 if non-numeric (for SUM/AVG)."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _is_numeric(val: Any) -> bool:
    """Return True if val can be used as a number."""
    if isinstance(val, (int, float)):
        return True
    if isinstance(val, str):
        try:
            float(val)
            return True
        except ValueError:
            return False
    return False


def _gather_numeric_args(func_args: List[Any], sheet: Any):
    """
    Flatten function arguments, expanding Range nodes, collecting float values.
    Returns (all_values, numeric_only_values) where:
      - all_values: every value (numeric replaced with float, strings kept)
      - numeric_values: only the numeric ones as floats
    """
    all_vals = []
    for arg in func_args:
        if isinstance(arg, Range):
            vals = _resolve_range(arg.start, arg.end, sheet)
            all_vals.extend(vals)
        else:
            all_vals.append(evaluate(arg, sheet))
    return all_vals


def _eval_func(node: FuncCall, sheet: Any) -> Any:
    name = node.name.upper()
    all_vals = _gather_numeric_args(node.args, sheet)

    if name in ('SUM', 'AVG', 'MIN', 'MAX'):
        if name in ('SUM', 'AVG'):
            # Non-numeric → 0.0 per spec
            floats = np.array([_to_float_or_zero(v) for v in all_vals], dtype=float)
            if len(floats) == 0:
                return 0.0
            if name == 'SUM':
                return float(np.sum(floats))
            else:  # AVG
                return float(np.mean(floats))
        else:
            # MIN / MAX: skip non-numeric cells
            numeric = [float(v) for v in all_vals if _is_numeric(v)]
            if not numeric:
                return 0.0
            arr = np.array(numeric, dtype=float)
            if name == 'MIN':
                return float(np.min(arr))
            else:
                return float(np.max(arr))

    raise ValueError(f"Unknown function: {name!r}")


def _eval_binop(node: BinOp, sheet: Any) -> float:
    left = evaluate(node.left, sheet)
    right = evaluate(node.right, sheet)
    op = node.op
    if op == '+':
        return float(left) + float(right)
    if op == '-':
        return float(left) - float(right)
    if op == '*':
        return float(left) * float(right)
    if op == '/':
        return float(left) / float(right)
    if op == '^':
        return float(left) ** float(right)
    raise ValueError(f"Unknown operator: {op!r}")


def _eval_if(node: IfExpr, sheet: Any) -> Any:
    lhs = evaluate(node.lhs, sheet)
    rhs = evaluate(node.rhs, sheet)
    op = node.cond_op

    # Numeric comparison where possible; fall back to string comparison
    try:
        l_val = float(lhs)
        r_val = float(rhs)
    except (TypeError, ValueError):
        l_val = lhs
        r_val = rhs

    if op == '=':
        condition = l_val == r_val
    elif op == '<>':
        condition = l_val != r_val
    elif op == '<':
        condition = l_val < r_val
    elif op == '<=':
        condition = l_val <= r_val
    elif op == '>':
        condition = l_val > r_val
    elif op == '>=':
        condition = l_val >= r_val
    else:
        raise ValueError(f"Unknown comparison operator: {op!r}")

    if condition:
        return evaluate(node.true_branch, sheet)
    else:
        return evaluate(node.false_branch, sheet)
