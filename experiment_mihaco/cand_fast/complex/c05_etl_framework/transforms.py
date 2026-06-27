"""transforms.py — Transform base class and subclasses for the ETL framework."""

from __future__ import annotations

import abc
import operator
from typing import Any

import pandas as pd


class Transform(abc.ABC):
    """Abstract base for all transform steps."""

    @abc.abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the transform and return the resulting DataFrame."""
        ...

    @abc.abstractmethod
    def validate(self, df: pd.DataFrame) -> None:
        """Raise ValueError if required columns are absent from df."""
        ...


class FilterRows(Transform):
    """Keep only rows where column op_kind value is true."""

    OP_MAP = {
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, column: str, op_kind: str, value: Any) -> None:
        self.column = column
        self.op_kind = op_kind
        self.value = value

    def validate(self, df: pd.DataFrame) -> None:
        if self.column not in df.columns:
            raise ValueError(
                f"filter: column '{self.column}' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate(df)
        op_func = self.OP_MAP[self.op_kind]

        # Try numeric cast; if successful, also cast column to numeric for comparison
        try:
            numeric_val = float(self.value)
            col_numeric = pd.to_numeric(df[self.column], errors="coerce")
            if col_numeric.notna().all():
                mask = op_func(col_numeric, numeric_val)
            else:
                # Column has non-numeric values — fall back to string comparison
                mask = op_func(df[self.column], self.value)
        except (ValueError, TypeError):
            # value is not numeric — compare as string
            mask = op_func(df[self.column], self.value)

        return df[mask].reset_index(drop=True)


class RenameColumns(Transform):
    """Rename columns according to a mapping; missing keys are silently skipped."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def validate(self, df: pd.DataFrame) -> None:
        # Per spec: raise ValueError if any rename source key does not exist
        missing = [k for k in self.mapping if k not in df.columns]
        if missing:
            raise ValueError(
                f"rename: source column(s) {missing} not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # df.rename silently skips keys not in df; we've already validated above
        return df.rename(columns=self.mapping)


class DeriveColumn(Transform):
    """Add a new column using df.eval(expr)."""

    def __init__(self, column: str, expr: str) -> None:
        self.column = column
        self.expr = expr

    def validate(self, df: pd.DataFrame) -> None:
        # derive: no explicit column validation required by spec
        # (the expr may reference existing columns; errors surface naturally)
        pass

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df[self.column] = df.eval(self.expr)
        return df


class Aggregate(Transform):
    """Group by columns and aggregate; result contains only group_by + agg columns."""

    def __init__(self, group_by: list[str], agg: dict[str, str]) -> None:
        self.group_by = group_by
        self.agg = agg  # {column: func_name}

    def validate(self, df: pd.DataFrame) -> None:
        # Spec: validate group_by and agg keys at the time the step is applied
        missing_group = [c for c in self.group_by if c not in df.columns]
        if missing_group:
            raise ValueError(
                f"aggregate: group_by column(s) {missing_group} not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )
        missing_agg = [c for c in self.agg if c not in df.columns]
        if missing_agg:
            raise ValueError(
                f"aggregate: agg column(s) {missing_agg} not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate(df)
        agg_cols = list(self.agg.keys())
        result = (
            df.groupby(self.group_by)[agg_cols]
            .agg(self.agg)
            .reset_index()
        )
        return result


def build_transform(step_op: str, params: dict[str, Any]) -> Transform:
    """Instantiate a Transform from an op name and params dict."""
    cls = REGISTRY.get(step_op)
    if cls is None:
        raise ValueError(f"Unknown transform op: '{step_op}'")
    return cls(**params)


REGISTRY: dict[str, type] = {
    "filter": FilterRows,
    "rename": RenameColumns,
    "derive": DeriveColumn,
    "aggregate": Aggregate,
}
