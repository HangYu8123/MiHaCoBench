"""
evaluator.py — AST evaluator for the mini spreadsheet formula language.

Public API:
  eval_node(node, sheet, visiting: set) -> float | str

The `sheet` object must support `_get(ref, visiting)`.

AVG semantics (per spec): Non-numeric cells count as 0.0 (affect denominator).
MIN/MAX semantics: Non-numeric cells are skipped entirely.
"""

import numpy as np
from parser import (
    NumNode, StrNode, CellNode, RangeNode,
    BinOpNode, UnaryNode, FuncNode, IfNode,
)


def _expand_range(range_ref: str) -> list[str]:
    """
    Expand a range like 'A1:B3' into a list of cell refs:
    ['A1', 'A2', 'A3', 'B1', 'B2', 'B3']

    Column order: iterate columns from start_col to end_col,
    and for each column iterate rows from start_row to end_row.
    """
    left, right = range_ref.split(':')
    start_col, start_row = _split_ref(left)
    end_col, end_row = _split_ref(right)

    start_col_idx = _col_to_idx(start_col)
    end_col_idx = _col_to_idx(end_col)

    refs = []
    for col_idx in range(start_col_idx, end_col_idx + 1):
        col_str = _idx_to_col(col_idx)
        for row in range(start_row, end_row + 1):
            refs.append(f"{col_str}{row}")

    return refs


def _split_ref(ref: str) -> tuple[str, int]:
    """Split 'AA10' into ('AA', 10)."""
    i = 0
    while i < len(ref) and ref[i].isalpha():
        i += 1
    return ref[:i], int(ref[i:])


def _col_to_idx(col: str) -> int:
    """Convert column letters to zero-based index. A=0, B=1, ..., Z=25, AA=26."""
    idx = 0
    for c in col:
        idx = idx * 26 + (ord(c) - ord('A') + 1)
    return idx - 1  # zero-based


def _idx_to_col(idx: int) -> str:
    """Convert zero-based index to column letters. 0=A, 25=Z, 26=AA."""
    result = []
    n = idx + 1  # 1-based
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result.append(chr(ord('A') + rem))
    return ''.join(reversed(result))


def _is_numeric(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def eval_node(node, sheet, visiting: set):
    """Recursively evaluate an AST node against a sheet."""

    if isinstance(node, NumNode):
        return node.value

    if isinstance(node, StrNode):
        return node.value

    if isinstance(node, CellNode):
        return sheet._get(node.ref, visiting)

    if isinstance(node, RangeNode):
        refs = _expand_range(node.ref)
        return [sheet._get(ref, visiting) for ref in refs]

    if isinstance(node, UnaryNode):
        val = eval_node(node.operand, sheet, visiting)
        if node.op == '-':
            return -float(val)
        return val

    if isinstance(node, BinOpNode):
        left = eval_node(node.left, sheet, visiting)
        right = eval_node(node.right, sheet, visiting)

        op = node.op

        # Arithmetic operators
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

        # Comparison operators — return Python bool (truthy for IF)
        if op == '=':
            return left == right
        if op == '<>':
            return left != right
        if op == '<':
            return float(left) < float(right)
        if op == '<=':
            return float(left) <= float(right)
        if op == '>':
            return float(left) > float(right)
        if op == '>=':
            return float(left) >= float(right)

        raise ValueError(f"Unknown operator: {op!r}")

    if isinstance(node, IfNode):
        cond_val = eval_node(node.cond, sheet, visiting)
        if cond_val:
            return eval_node(node.true_branch, sheet, visiting)
        else:
            return eval_node(node.false_branch, sheet, visiting)

    if isinstance(node, FuncNode):
        name = node.name

        # Collect all values from args (args may be RangeNode → list, or scalar)
        all_values = []
        for arg in node.args:
            val = eval_node(arg, sheet, visiting)
            if isinstance(val, list):
                all_values.extend(val)
            else:
                all_values.append(val)

        if name == 'SUM':
            # Non-numeric treated as 0.0
            numeric_vals = [float(v) if _is_numeric(v) else 0.0 for v in all_values]
            if not numeric_vals:
                return 0.0
            return float(np.sum(numeric_vals))

        if name == 'AVG':
            # Per spec: non-numeric treated as 0.0 (affects denominator)
            numeric_vals = [float(v) if _is_numeric(v) else 0.0 for v in all_values]
            if not numeric_vals:
                return 0.0
            return float(np.mean(numeric_vals))

        if name == 'MIN':
            # Non-numeric cells are ignored (skipped)
            numeric_vals = [float(v) for v in all_values if _is_numeric(v)]
            if not numeric_vals:
                return 0.0
            return float(np.min(numeric_vals))

        if name == 'MAX':
            # Non-numeric cells are ignored (skipped)
            numeric_vals = [float(v) for v in all_values if _is_numeric(v)]
            if not numeric_vals:
                return 0.0
            return float(np.max(numeric_vals))

        raise ValueError(f"Unknown function: {name!r}")

    raise ValueError(f"Unknown AST node type: {type(node)}")
