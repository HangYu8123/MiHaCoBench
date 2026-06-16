"""
evaluator.py — AST evaluator for the spreadsheet formula language.

The evaluator walks the AST returned by parser.parse() and computes a
float | str result.  It calls back into the Sheet via sheet.get_value()
for cell references, which enables lazy evaluation and cycle detection.
"""

import numpy as np

from parser import (
    NumberNode, StringNode, CellRefNode, RangeNode,
    BinOpNode, UnaryMinusNode, FuncCallNode, IfNode,
)


# ---------------------------------------------------------------------------
# Column / row helpers
# ---------------------------------------------------------------------------

def col_to_index(col: str) -> int:
    """
    Convert a column letter string to a 1-based integer index.
    'A' -> 1, 'Z' -> 26, 'AA' -> 27, 'AB' -> 28, …
    (Bijective base-26 numbering.)
    """
    result = 0
    for ch in col:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result


def index_to_col(index: int) -> str:
    """Inverse of col_to_index: 1 -> 'A', 27 -> 'AA', …"""
    letters = []
    while index > 0:
        index, rem = divmod(index - 1, 26)
        letters.append(chr(ord('A') + rem))
    return ''.join(reversed(letters))


def _split_ref(ref: str):
    """Split 'AA10' into ('AA', 10)."""
    i = 0
    while i < len(ref) and ref[i].isalpha():
        i += 1
    return ref[:i], int(ref[i:])


def expand_range(range_str: str):
    """
    Expand 'A1:B3' into ['A1', 'A2', 'A3', 'B1', 'B2', 'B3'].
    Column-major order (iterate columns in outer loop).
    """
    left, right = range_str.split(':')
    col1, row1 = _split_ref(left)
    col2, row2 = _split_ref(right)
    c1 = col_to_index(col1)
    c2 = col_to_index(col2)
    r1 = min(row1, row2)
    r2 = max(row1, row2)
    if c1 > c2:
        c1, c2 = c2, c1
    cells = []
    for ci in range(c1, c2 + 1):
        col_str = index_to_col(ci)
        for ri in range(r1, r2 + 1):
            cells.append(f"{col_str}{ri}")
    return cells


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def evaluate(node, sheet) -> 'float | str':
    """
    Recursively evaluate *node* against *sheet*.
    *sheet* must implement .get_value(ref) -> float | str.
    """

    if isinstance(node, NumberNode):
        return float(node.value)

    if isinstance(node, StringNode):
        return node.value

    if isinstance(node, CellRefNode):
        return sheet.get_value(node.ref)

    if isinstance(node, RangeNode):
        # A bare RangeNode outside of a function call would be an error,
        # but we handle it gracefully by returning the first cell's value.
        cells = expand_range(node.ref)
        if not cells:
            return 0.0
        return sheet.get_value(cells[0])

    if isinstance(node, UnaryMinusNode):
        val = evaluate(node.operand, sheet)
        return -float(val)

    if isinstance(node, BinOpNode):
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
        raise ValueError(f"Unknown binary operator: {op!r}")

    if isinstance(node, FuncCallNode):
        return _eval_func(node, sheet)

    if isinstance(node, IfNode):
        return _eval_if(node, sheet)

    raise ValueError(f"Unknown AST node type: {type(node)}")


# ---------------------------------------------------------------------------
# Function call evaluation
# ---------------------------------------------------------------------------

def _collect_numeric_values(args, sheet) -> list:
    """
    Collect numeric values from a list of argument nodes.
    RangeNode → expand and get_value each cell, skip non-numeric.
    Other nodes → evaluate and include if numeric.
    """
    values = []
    for arg in args:
        if isinstance(arg, RangeNode):
            for ref in expand_range(arg.ref):
                val = sheet.get_value(ref)
                try:
                    values.append(float(val))
                except (TypeError, ValueError):
                    pass  # skip non-numeric
        else:
            val = evaluate(arg, sheet)
            try:
                values.append(float(val))
            except (TypeError, ValueError):
                pass  # skip non-numeric
    return values


def _eval_func(node: FuncCallNode, sheet) -> float:
    name = node.name
    values = _collect_numeric_values(node.args, sheet)

    if not values:
        if name in ('MIN', 'MAX'):
            raise ValueError(f"{name} called with no numeric values")
        return 0.0

    arr = np.array(values, dtype=float)

    if name == 'SUM':
        return float(np.sum(arr))
    if name == 'AVG':
        return float(np.mean(arr))
    if name == 'MIN':
        return float(np.min(arr))
    if name == 'MAX':
        return float(np.max(arr))

    raise ValueError(f"Unknown function: {name!r}")


# ---------------------------------------------------------------------------
# IF evaluation
# ---------------------------------------------------------------------------

_COMP_OPS = {
    '=':  lambda a, b: a == b,
    '<>': lambda a, b: a != b,
    '<':  lambda a, b: a < b,
    '<=': lambda a, b: a <= b,
    '>':  lambda a, b: a > b,
    '>=': lambda a, b: a >= b,
}


def _eval_if(node: IfNode, sheet) -> 'float | str':
    lhs = evaluate(node.lhs, sheet)
    rhs = evaluate(node.rhs, sheet)

    # Try numeric comparison; fall back to string comparison
    try:
        l_num = float(lhs)
        r_num = float(rhs)
        condition = _COMP_OPS[node.cond_op](l_num, r_num)
    except (TypeError, ValueError):
        condition = _COMP_OPS[node.cond_op](lhs, rhs)

    if condition:
        return evaluate(node.true_val, sheet)
    else:
        return evaluate(node.false_val, sheet)
