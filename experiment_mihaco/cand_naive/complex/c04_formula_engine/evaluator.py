"""
evaluator.py — Walks the AST and evaluates it against a Sheet.
"""

import re
import numpy as np

from parser import (
    NumLiteral, StrLiteral, CellRef, RangeRef,
    BinOp, UnaryMinus, FuncCall, IfExpr,
    parse_formula,
)


_REF_PATTERN = re.compile(r"^([A-Z]+)(\d+)$")


def _col_index(letters: str) -> int:
    """Convert column letters to a 0-based column index (A=0, B=1, …)."""
    result = 0
    for ch in letters:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result - 1


def _expand_range(range_str: str) -> list[str]:
    """
    Expand 'A1:B3' into a list of cell references.
    Top-left and bottom-right are determined by col/row ordering.
    """
    left, right = range_str.split(':')
    m1 = _REF_PATTERN.match(left)
    m2 = _REF_PATTERN.match(right)
    if not m1 or not m2:
        raise ValueError(f"Invalid range: {range_str}")
    col1 = _col_index(m1.group(1))
    row1 = int(m1.group(2))
    col2 = _col_index(m2.group(1))
    row2 = int(m2.group(2))

    min_col, max_col = min(col1, col2), max(col1, col2)
    min_row, max_row = min(row1, row2), max(row1, row2)

    refs = []
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            col_letters = _col_num_to_letters(c)
            refs.append(f"{col_letters}{r}")
    return refs


def _col_num_to_letters(c: int) -> str:
    """Convert 0-based column index back to letters."""
    letters = []
    c += 1
    while c > 0:
        c, rem = divmod(c - 1, 26)
        letters.append(chr(ord('A') + rem))
    return ''.join(reversed(letters))


def evaluate(node, sheet, visiting: set | None = None) -> float | str:
    """
    Recursively evaluate an AST node in the context of *sheet*.

    *visiting* tracks the set of cell refs currently on the call stack
    for cycle detection. It is managed externally by the Sheet when
    evaluating a whole cell.
    """
    if visiting is None:
        visiting = set()

    if isinstance(node, NumLiteral):
        return float(node.value)

    if isinstance(node, StrLiteral):
        return node.value

    if isinstance(node, CellRef):
        ref = node.ref
        if ref in visiting:
            raise ValueError(f"Circular reference detected involving {ref}")
        return sheet._eval_cell(ref, visiting)

    if isinstance(node, RangeRef):
        # Ranges are only valid inside function calls; if we get here bare,
        # just return the range string (should not happen in valid formulas).
        return node.range_str

    if isinstance(node, UnaryMinus):
        val = evaluate(node.operand, sheet, visiting)
        return -float(val)

    if isinstance(node, BinOp):
        left  = evaluate(node.left,  sheet, visiting)
        right = evaluate(node.right, sheet, visiting)
        l = float(left)
        r = float(right)
        op = node.op
        if op == '+': return l + r
        if op == '-': return l - r
        if op == '*': return l * r
        if op == '/': return l / r
        if op == '^': return float(l ** r)
        raise ValueError(f"Unknown operator {op}")

    if isinstance(node, FuncCall):
        return _eval_func(node.name, node.args, sheet, visiting)

    if isinstance(node, IfExpr):
        return _eval_if(node, sheet, visiting)

    raise TypeError(f"Unknown AST node type: {type(node)}")


def _get_numeric_values(args: list, sheet, visiting: set) -> list[float]:
    """Collect numeric values from a list of arg nodes (ranges, refs, exprs)."""
    values = []
    for arg in args:
        if isinstance(arg, RangeRef):
            refs = _expand_range(arg.range_str)
            for ref in refs:
                try:
                    v = sheet._eval_cell(ref, visiting)
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass  # skip non-numeric
        else:
            v = evaluate(arg, sheet, visiting)
            try:
                values.append(float(v))
            except (ValueError, TypeError):
                pass
    return values


def _eval_func(name: str, args: list, sheet, visiting: set) -> float:
    if name == "SUM":
        vals = _get_numeric_values(args, sheet, visiting)
        return float(np.sum(vals)) if vals else 0.0
    if name == "AVG":
        vals = _get_numeric_values(args, sheet, visiting)
        return float(np.mean(vals)) if vals else 0.0
    if name == "MIN":
        vals = _get_numeric_values(args, sheet, visiting)
        return float(np.min(vals)) if vals else 0.0
    if name == "MAX":
        vals = _get_numeric_values(args, sheet, visiting)
        return float(np.max(vals)) if vals else 0.0
    raise ValueError(f"Unknown function: {name}")


def _eval_if(node: IfExpr, sheet, visiting: set) -> float | str:
    left  = evaluate(node.left,  sheet, visiting)
    right = evaluate(node.right, sheet, visiting)

    # Try numeric comparison, fall back to string
    try:
        l = float(left)
        r = float(right)
    except (ValueError, TypeError):
        l = left
        r = right

    op = node.cmp_op
    if   op == '=':  cond = l == r
    elif op == '<>': cond = l != r
    elif op == '<':  cond = l <  r
    elif op == '<=': cond = l <= r
    elif op == '>':  cond = l >  r
    elif op == '>=': cond = l >= r
    else:
        raise ValueError(f"Unknown comparison operator: {op}")

    branch = node.true_val if cond else node.false_val
    return evaluate(branch, sheet, visiting)
