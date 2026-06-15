"""AST evaluator for the formula engine.

The :func:`evaluate` function walks an AST node produced by :mod:`parser` and
resolves it to a Python ``float`` or ``str``.  It receives a callback
``cell_value(ref: str) -> float | str`` for resolving cell references so that
it remains decoupled from the Sheet internals.

Range aggregation uses numpy for correctness and efficiency:
    SUM, AVG (mean), MIN, MAX
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np

from parser import (
    NumLiteral, StrLiteral, CellRef, RangeRef, BinOp, UnaryMinus,
    FuncCall, IfExpr,
)

# Type alias for the cell-lookup callback.
CellGetter = Callable[[str], "float | str"]


# ---------------------------------------------------------------------------
# Range utilities
# ---------------------------------------------------------------------------

def _col_index(letters: str) -> int:
    """Convert 'A' → 1, 'B' → 2, 'AA' → 27, etc. (1-based)."""
    result = 0
    for ch in letters:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result


def _col_letters(index: int) -> str:
    """Inverse of _col_index; 1 → 'A', 27 → 'AA'."""
    out = []
    while index > 0:
        index, rem = divmod(index - 1, 26)
        out.append(chr(rem + ord("A")))
    return "".join(reversed(out))


def _range_refs(start: str, end: str) -> list[str]:
    """Enumerate all cell references within the rectangular range start:end."""
    import re
    m_s = re.match(r"([A-Z]+)([0-9]+)$", start)
    m_e = re.match(r"([A-Z]+)([0-9]+)$", end)
    if not m_s or not m_e:
        raise ValueError(f"Invalid range: {start}:{end}")
    col_s = _col_index(m_s.group(1))
    row_s = int(m_s.group(2))
    col_e = _col_index(m_e.group(1))
    row_e = int(m_e.group(2))
    refs = []
    for row in range(min(row_s, row_e), max(row_s, row_e) + 1):
        for col in range(min(col_s, col_e), max(col_s, col_e) + 1):
            refs.append(f"{_col_letters(col)}{row}")
    return refs


def _collect_numerics(args: list[Any], getter: CellGetter) -> np.ndarray:
    """Resolve a list of AST args (ranges + cells + literals) to a float array."""
    values: list[float] = []
    for arg in args:
        if isinstance(arg, RangeRef):
            for ref in _range_refs(arg.start, arg.end):
                v = getter(ref)
                if isinstance(v, (int, float)):
                    values.append(float(v))
                else:
                    try:
                        values.append(float(v))
                    except (TypeError, ValueError):
                        values.append(0.0)
        else:
            v = evaluate(arg, getter)
            try:
                values.append(float(v))
            except (TypeError, ValueError):
                values.append(0.0)
    return np.array(values, dtype=float)


# ---------------------------------------------------------------------------
# Comparison operator helpers
# ---------------------------------------------------------------------------

_CMP_FUNCS: dict[str, Callable[[Any, Any], bool]] = {
    "=":  lambda a, b: a == b,
    "<>": lambda a, b: a != b,
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">":  lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------

def evaluate(node: Any, getter: CellGetter) -> "float | str":
    """Recursively evaluate *node* and return a ``float`` or ``str``."""

    if isinstance(node, NumLiteral):
        return node.value

    if isinstance(node, StrLiteral):
        return node.value

    if isinstance(node, CellRef):
        return getter(node.ref)

    if isinstance(node, UnaryMinus):
        v = evaluate(node.operand, getter)
        return -float(v)

    if isinstance(node, BinOp):
        left = evaluate(node.left, getter)
        right = evaluate(node.right, getter)
        op = node.op
        lf = float(left)
        rf = float(right)
        if op == "+":
            return lf + rf
        if op == "-":
            return lf - rf
        if op == "*":
            return lf * rf
        if op == "/":
            if rf == 0.0:
                raise ZeroDivisionError("Division by zero in formula")
            return lf / rf
        if op == "^":
            return lf ** rf
        raise ValueError(f"Unknown binary operator: {op!r}")

    if isinstance(node, FuncCall):
        name = node.name
        if name == "SUM":
            arr = _collect_numerics(node.args, getter)
            return float(np.sum(arr))
        if name == "AVG":
            arr = _collect_numerics(node.args, getter)
            if len(arr) == 0:
                return 0.0
            return float(np.mean(arr))
        if name == "MIN":
            arr = _collect_numerics(node.args, getter)
            if len(arr) == 0:
                return 0.0
            return float(np.min(arr))
        if name == "MAX":
            arr = _collect_numerics(node.args, getter)
            if len(arr) == 0:
                return 0.0
            return float(np.max(arr))
        raise ValueError(f"Unknown function: {name!r}")

    if isinstance(node, IfExpr):
        cl = evaluate(node.cond_left, getter)
        cr = evaluate(node.cond_right, getter)
        fn = _CMP_FUNCS.get(node.cond_op)
        if fn is None:
            raise ValueError(f"Unknown comparison operator: {node.cond_op!r}")
        try:
            condition = fn(float(cl), float(cr))
        except (TypeError, ValueError):
            condition = fn(cl, cr)
        return evaluate(node.true_expr if condition else node.false_expr, getter)

    if isinstance(node, RangeRef):
        raise ValueError(
            f"RangeRef {node.start}:{node.end} used outside a function call"
        )

    raise ValueError(f"Unknown AST node type: {type(node).__name__}")
