"""Execution engine for the mini-SQL dialect (gold reference).

Holds the in-memory tables and executes a parsed statement AST. This module
owns every *semantic* rule of the contract:

* CREATE TABLE (duplicate => ValueError),
* INSERT with per-column INT/TEXT type checking, positional or named,
* SELECT with three-valued (Kleene) WHERE logic, GROUP BY + aggregates,
  ORDER BY (multi-key, stable, NULLs-first-ASC / NULLs-last-DESC),
  DISTINCT, and LIMIT/OFFSET.

Unknown tables/columns, type mismatches, and invalid GROUP BY all raise
``ValueError``.
"""
from __future__ import annotations

from typing import Optional

from sqlparser import (
    parse,
    CreateTable, Insert, Select, SelectItem, Column, Aggregate,
    Compare, IsNull, Not, And, Or, OrderKey,
)

# Three-valued logic uses Python's True / False / None, where None == UNKNOWN.
UNKNOWN = None


class _Table:
    def __init__(self, columns: list):
        self.column_names = [c for c, _ in columns]
        self.column_types = {c: t for c, t in columns}
        self.rows: list[dict] = []


class Engine:
    """Owns the table catalog and executes statements."""

    def __init__(self):
        self.tables: dict[str, _Table] = {}

    # ------------------------------------------------------------------ #
    # Public entry
    # ------------------------------------------------------------------ #
    def execute(self, sql: str):
        node = parse(sql)
        if isinstance(node, CreateTable):
            return self._exec_create(node)
        if isinstance(node, Insert):
            return self._exec_insert(node)
        if isinstance(node, Select):
            return self._exec_select(node)
        raise ValueError("unsupported statement")  # pragma: no cover

    # ------------------------------------------------------------------ #
    # CREATE TABLE
    # ------------------------------------------------------------------ #
    def _exec_create(self, node: CreateTable):
        if node.table in self.tables:
            raise ValueError(f"table {node.table!r} already exists")
        seen = set()
        for name, _ in node.columns:
            if name in seen:
                raise ValueError(f"duplicate column {name!r}")
            seen.add(name)
        self.tables[node.table] = _Table(node.columns)
        return None

    # ------------------------------------------------------------------ #
    # INSERT
    # ------------------------------------------------------------------ #
    def _exec_insert(self, node: Insert):
        table = self.tables.get(node.table)
        if table is None:
            raise ValueError(f"unknown table {node.table!r}")
        if node.columns is None:
            cols = list(table.column_names)
        else:
            cols = node.columns
            for c in cols:
                if c not in table.column_types:
                    raise ValueError(f"unknown column {c!r}")
            if len(set(cols)) != len(cols):
                raise ValueError("duplicate column in INSERT column list")
        values = [v.value for v in node.values]
        if len(values) != len(cols):
            raise ValueError("number of values does not match number of columns")
        row: dict = {c: None for c in table.column_names}
        for c, val in zip(cols, values):
            self._check_type(table.column_types[c], val, c)
            row[c] = val
        table.rows.append(row)
        return None

    @staticmethod
    def _check_type(col_type: str, value: object, col_name: str) -> None:
        if value is None:
            return  # all columns nullable
        if col_type == "INT":
            # bool is a subclass of int but never produced by the tokenizer;
            # reject defensively so only true integers pass.
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"column {col_name!r} is INT but value is not an integer")
        elif col_type == "TEXT":
            if not isinstance(value, str):
                raise ValueError(f"column {col_name!r} is TEXT but value is not a string")
        else:  # pragma: no cover - parser only emits INT/TEXT
            raise ValueError(f"unknown column type {col_type!r}")

    # ------------------------------------------------------------------ #
    # SELECT
    # ------------------------------------------------------------------ #
    def _exec_select(self, node: Select):
        table = self.tables.get(node.table)
        if table is None:
            raise ValueError(f"unknown table {node.table!r}")
        coltypes = table.column_types

        # 1) WHERE filter (three-valued logic; keep only rows evaluating TRUE).
        if node.where is not None:
            self._validate_condition_columns(node.where, coltypes)
            filtered = [r for r in table.rows
                        if self._eval_condition(node.where, r, coltypes) is True]
        else:
            filtered = list(table.rows)

        has_agg = self._select_has_aggregate(node.select_list)

        # Each result row carries a parallel "sort context" dict from which
        # ORDER BY values are resolved: base-table columns for a plain
        # projection, and grouped-column values (plus the result fields) for a
        # grouped query. This lets ORDER BY name a base column even when it is
        # not in the select list (standard SQL behaviour).
        if node.group_by is not None:
            for c in node.group_by:
                if c not in coltypes:
                    raise ValueError(f"unknown column in GROUP BY: {c!r}")
            result_rows, contexts = self._select_grouped(node, filtered, coltypes, node.group_by)
        elif has_agg:
            # Whole filtered table is a single group (one row even if empty).
            result_rows, contexts = self._select_grouped(node, filtered, coltypes, group_by=None)
        else:
            result_rows, contexts = self._select_projection(node, filtered, coltypes)

        # DISTINCT applies before ORDER BY / LIMIT / OFFSET.
        if node.distinct:
            result_rows, contexts = self._distinct(result_rows, contexts)

        # ORDER BY.
        if node.order_by is not None:
            result_rows = self._order(result_rows, contexts, node.order_by, coltypes)

        # OFFSET then LIMIT (both after ordering).
        result_rows = self._limit_offset(result_rows, node.limit, node.offset)
        return result_rows

    # --- select-list helpers ------------------------------------------ #
    @staticmethod
    def _select_has_aggregate(select_list) -> bool:
        if select_list == "*":
            return False
        return any(isinstance(it.expr, Aggregate) for it in select_list)

    def _result_key(self, item: SelectItem) -> str:
        return item.alias if item.alias is not None else item.text

    def _select_projection(self, node: Select, rows: list, coltypes: dict):
        """Plain projection: no GROUP BY, no aggregates.

        Returns ``(result_rows, contexts)`` where each context is the originating
        source row (so ORDER BY can reference any base column).
        """
        if node.select_list == "*":
            cols = list(self.tables[node.table].column_names)
            result = [{c: r[c] for c in cols} for r in rows]
            return result, list(rows)
        # validate referenced columns
        for it in node.select_list:
            self._check_column_expr(it.expr, coltypes)
        out = []
        contexts = []
        for r in rows:
            row_out = {}
            for it in node.select_list:
                row_out[self._result_key(it)] = r[it.expr.name]
            out.append(row_out)
            contexts.append(r)
        return out, contexts

    def _check_column_expr(self, expr, coltypes: dict) -> None:
        if isinstance(expr, Column):
            if expr.name not in coltypes:
                raise ValueError(f"unknown column {expr.name!r}")
        elif isinstance(expr, Aggregate):
            if expr.arg != "*" and expr.arg not in coltypes:
                raise ValueError(f"unknown column {expr.arg!r}")

    # --- grouping + aggregates ---------------------------------------- #
    def _select_grouped(self, node: Select, rows: list, coltypes: dict,
                         group_by: Optional[list]):
        """Grouped / whole-table aggregation.

        Returns ``(result_rows, contexts)``; each context maps every grouped
        column name to that group's value plus all result fields, so ORDER BY
        may name a grouped column or an aggregate alias.
        """
        if node.select_list == "*":
            raise ValueError("SELECT * is not allowed with GROUP BY/aggregates")
        # Validate the select list against GROUP BY rules.
        gb = group_by or []
        for it in node.select_list:
            self._check_column_expr(it.expr, coltypes)
            if isinstance(it.expr, Column) and it.expr.name not in gb:
                raise ValueError(
                    f"column {it.expr.name!r} must appear in GROUP BY or an aggregate"
                )

        if group_by is None:
            groups = [(None, rows)]  # exactly one group, even when rows == []
        else:
            order: list = []
            buckets: dict = {}
            for r in rows:
                key = tuple(r[c] for c in group_by)  # NULL is its own group key
                if key not in buckets:
                    buckets[key] = []
                    order.append(key)
                buckets[key].append(r)
            groups = [(k, buckets[k]) for k in order]

        out = []
        contexts = []
        for key, grp in groups:
            row_out = {}
            for it in node.select_list:
                k = self._result_key(it)
                if isinstance(it.expr, Aggregate):
                    row_out[k] = self._aggregate(it.expr, grp)
                else:  # grouped column
                    idx = group_by.index(it.expr.name)
                    row_out[k] = key[idx]
            ctx = dict(row_out)
            if group_by is not None:
                for i, c in enumerate(group_by):
                    ctx[c] = key[i]
            out.append(row_out)
            contexts.append(ctx)
        return out, contexts

    @staticmethod
    def _aggregate(agg: Aggregate, rows: list):
        func = agg.func
        if func == "COUNT":
            if agg.arg == "*":
                return len(rows)
            return sum(1 for r in rows if r[agg.arg] is not None)
        vals = [r[agg.arg] for r in rows if r[agg.arg] is not None]
        if func == "SUM":
            if not vals:
                return None
            return sum(vals)
        if func == "AVG":
            if not vals:
                return None
            return sum(vals) / len(vals)  # real division -> float
        if func == "MIN":
            if not vals:
                return None
            return min(vals)
        if func == "MAX":
            if not vals:
                return None
            return max(vals)
        raise ValueError(f"unknown aggregate {func!r}")  # pragma: no cover

    # --- DISTINCT ------------------------------------------------------ #
    @staticmethod
    def _distinct(rows: list, contexts: list):
        """Drop duplicate result rows (NULL == NULL for this purpose), keeping
        the first occurrence and its parallel sort context."""
        seen = set()
        out = []
        out_ctx = []
        for r, ctx in zip(rows, contexts):
            # Two rows are duplicates iff every selected value is equal; None
            # compares equal to None. Include the key names so differently
            # shaped rows can never collide.
            sig = (tuple(r.keys()), tuple(r[k] for k in r))
            if sig not in seen:
                seen.add(sig)
                out.append(r)
                out_ctx.append(ctx)
        return out, out_ctx

    # --- ORDER BY ------------------------------------------------------ #
    def _order(self, rows: list, contexts: list, order_by: list, coltypes: dict) -> list:
        for key in order_by:
            if key.col not in coltypes:
                raise ValueError(f"unknown column in ORDER BY: {key.col!r}")
        # The sort value for each key is resolved from the row's *context*: base
        # columns for a plain projection, grouped columns / aggregate fields for
        # a grouped query. ORDER BY may therefore name a base column even when it
        # is not in the select list.
        def sort_value(ctx, col):
            if col in ctx:
                return ctx[col]
            raise ValueError(f"ORDER BY column {col!r} is not available")

        decorated = list(zip(rows, contexts))
        # Apply keys right-to-left; Python's sort is stable, so the leftmost key
        # ends up most significant and ties preserve prior (insertion) order.
        for key in reversed(order_by):
            decorated.sort(key=lambda pair, k=key: self._sort_rank(
                sort_value(pair[1], k.col), k.descending))
        return [r for r, _ in decorated]

    @staticmethod
    def _sort_rank(value, descending: bool):
        """Return a sort key tuple implementing NULL ordering.

        Contract: NULLs sort BEFORE non-NULLs under ASC, and AFTER non-NULLs
        under DESC. We map each value to ``(null_flag, value)``; ``null_flag``
        is chosen so that, after Python's ascending tuple sort (with the
        non-null component negated/inverted for DESC), NULLs land on the
        correct side.

        For ASC: NULL -> (0, _) sorts before non-NULL -> (1, value).
        For DESC: we sort with reverse semantics via a custom comparator, so we
        emit a key that, when sorted *ascending*, yields descending data with
        NULLs last. We achieve that by inverting both the flag and the value.
        """
        is_null = value is None
        if not descending:
            # ascending: nulls first
            if is_null:
                return (0,)
            return (1, _Ordered(value, reverse=False))
        # descending: nulls last
        if is_null:
            return (1,)
        return (0, _Ordered(value, reverse=True))

    # --- LIMIT / OFFSET ------------------------------------------------ #
    @staticmethod
    def _limit_offset(rows: list, limit: Optional[int], offset: Optional[int]) -> list:
        if offset is not None:
            if offset < 0:
                raise ValueError("OFFSET must be non-negative")
            rows = rows[offset:]
        if limit is not None:
            if limit < 0:
                raise ValueError("LIMIT must be non-negative")
            rows = rows[:limit]
        return rows

    # ------------------------------------------------------------------ #
    # WHERE evaluation (three-valued / Kleene logic)
    # ------------------------------------------------------------------ #
    def _validate_condition_columns(self, cond, coltypes: dict) -> None:
        if isinstance(cond, Compare):
            if cond.col not in coltypes:
                raise ValueError(f"unknown column {cond.col!r}")
        elif isinstance(cond, IsNull):
            if cond.col not in coltypes:
                raise ValueError(f"unknown column {cond.col!r}")
        elif isinstance(cond, Not):
            self._validate_condition_columns(cond.operand, coltypes)
        elif isinstance(cond, (And, Or)):
            self._validate_condition_columns(cond.left, coltypes)
            self._validate_condition_columns(cond.right, coltypes)

    def _eval_condition(self, cond, row: dict, coltypes: dict):
        """Return True / False / UNKNOWN(None) under Kleene logic."""
        if isinstance(cond, Compare):
            return self._eval_compare(cond, row, coltypes)
        if isinstance(cond, IsNull):
            is_null = row[cond.col] is None
            result = (not is_null) if cond.negated else is_null
            return result  # always TRUE/FALSE, never UNKNOWN
        if isinstance(cond, Not):
            v = self._eval_condition(cond.operand, row, coltypes)
            if v is UNKNOWN:
                return UNKNOWN
            return not v
        if isinstance(cond, And):
            a = self._eval_condition(cond.left, row, coltypes)
            b = self._eval_condition(cond.right, row, coltypes)
            return _kleene_and(a, b)
        if isinstance(cond, Or):
            a = self._eval_condition(cond.left, row, coltypes)
            b = self._eval_condition(cond.right, row, coltypes)
            return _kleene_or(a, b)
        raise ValueError("invalid condition")  # pragma: no cover

    def _eval_compare(self, cmp: Compare, row: dict, coltypes: dict):
        col_type = coltypes[cmp.col]
        lit = cmp.literal
        # Type compatibility between the column and the literal. NULL literal is
        # always type-compatible (and yields UNKNOWN). A non-NULL literal must
        # match the column's domain, else it is a type-mismatch ValueError.
        if lit is not None:
            lit_is_int = isinstance(lit, int) and not isinstance(lit, bool)
            lit_is_str = isinstance(lit, str)
            if col_type == "INT" and not lit_is_int:
                raise ValueError("type mismatch: INT column compared to non-int")
            if col_type == "TEXT" and not lit_is_str:
                raise ValueError("type mismatch: TEXT column compared to non-str")
        cell = row[cmp.col]
        if cell is None or lit is None:
            return UNKNOWN
        return _apply_op(cmp.op, cell, lit)


class _Ordered:
    """Wrapper giving a value the correct comparison direction for sorting.

    For ascending order we compare values naturally. For descending order we
    invert the comparison so the standard ascending tuple sort produces the
    values in descending sequence, keeping the sort stable.
    """

    __slots__ = ("value", "reverse")

    def __init__(self, value, reverse: bool):
        self.value = value
        self.reverse = reverse

    def __lt__(self, other: "_Ordered") -> bool:
        if self.reverse:
            return other.value < self.value
        return self.value < other.value

    def __eq__(self, other) -> bool:  # pragma: no cover - not needed for sort
        return isinstance(other, _Ordered) and self.value == other.value


# --------------------------------------------------------------------------- #
# Kleene truth tables and comparison
# --------------------------------------------------------------------------- #
def _kleene_and(a, b):
    if a is False or b is False:
        return False
    if a is UNKNOWN or b is UNKNOWN:
        return UNKNOWN
    return True


def _kleene_or(a, b):
    if a is True or b is True:
        return True
    if a is UNKNOWN or b is UNKNOWN:
        return UNKNOWN
    return False


def _apply_op(op: str, a, b) -> bool:
    if op == "=":
        return a == b
    if op == "<>":
        return a != b
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == ">":
        return a > b
    if op == ">=":
        return a >= b
    raise ValueError(f"unknown operator {op!r}")  # pragma: no cover
