"""
transforms.py — Transform base class + concrete subclasses + registry.
"""
from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from typing import Dict, Type

import pandas as pd

from config import (
    AggregateTransformConfig,
    DeriveTransformConfig,
    FilterTransformConfig,
    RenameTransformConfig,
    TransformConfig,
)

# Operator dispatch for filter comparisons
_OPS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


class TransformBase(ABC):
    """Abstract base class for all transform steps."""

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> None:
        """Raise ValueError if required columns are missing from df."""
        ...

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this transform to df and return the result."""
        ...


class FilterRows(TransformBase):
    """Keep only rows where column op_kind value is True."""

    def __init__(self, config: FilterTransformConfig) -> None:
        self.column = config.column
        self.op_kind = config.op_kind
        self.value = config.value

    def validate(self, df: pd.DataFrame) -> None:
        if self.column not in df.columns:
            raise ValueError(
                f"Filter: column {self.column!r} not found in DataFrame. "
                f"Available: {list(df.columns)}"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        op_fn = _OPS[self.op_kind]
        col = df[self.column]

        # Try to cast value to float for numeric comparison
        cast_value = self.value
        try:
            cast_value = float(self.value)
            col = col.astype(float)
        except (TypeError, ValueError):
            # Non-numeric: compare as-is (string comparison)
            cast_value = self.value

        mask = op_fn(col, cast_value)
        return df[mask].reset_index(drop=True)


class RenameColumns(TransformBase):
    """Rename columns according to mapping; missing keys are silently skipped."""

    def __init__(self, config: RenameTransformConfig) -> None:
        self.mapping = config.mapping

    def validate(self, df: pd.DataFrame) -> None:
        # Per spec: missing rename keys are silently skipped — no ValueError
        pass

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # pandas rename silently ignores missing keys by default
        return df.rename(columns=self.mapping)


class DeriveColumn(TransformBase):
    """Add a new column using df.eval(expr)."""

    def __init__(self, config: DeriveTransformConfig) -> None:
        self.column = config.column
        self.expr = config.expr

    def validate(self, df: pd.DataFrame) -> None:
        # No mandatory column validation for derive per spec
        pass

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # df.eval returns a Series when evaluating an expression
        result = df.eval(self.expr)
        df[self.column] = result
        return df


class Aggregate(TransformBase):
    """Group by columns and aggregate. Validates lazily at apply time."""

    def __init__(self, config: AggregateTransformConfig) -> None:
        self.group_by = config.group_by
        self.agg = config.agg  # {col: func_name}

    def validate(self, df: pd.DataFrame) -> None:
        """Validate that group_by and agg columns exist in df."""
        missing_group = [c for c in self.group_by if c not in df.columns]
        if missing_group:
            raise ValueError(
                f"Aggregate: group_by columns {missing_group} not found in DataFrame. "
                f"Available: {list(df.columns)}"
            )
        missing_agg = [c for c in self.agg if c not in df.columns]
        if missing_agg:
            raise ValueError(
                f"Aggregate: agg columns {missing_agg} not found in DataFrame. "
                f"Available: {list(df.columns)}"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Build agg func_dict preserving order
        func_dict = {col: func for col, func in self.agg.items()}

        agg_cols = list(func_dict.keys())
        grouped = df.groupby(self.group_by)[agg_cols].agg(func_dict).reset_index()

        # Ensure column order: group_by cols first, then agg cols
        col_order = list(self.group_by) + agg_cols
        # Only include columns that exist (defensive)
        col_order = [c for c in col_order if c in grouped.columns]
        return grouped[col_order]


# ── Transform registry ──────────────────────────────────────────────────────

TRANSFORM_REGISTRY: Dict[str, Type[TransformBase]] = {
    "filter": FilterRows,
    "rename": RenameColumns,
    "derive": DeriveColumn,
    "aggregate": Aggregate,
}


def build_transform(config: TransformConfig) -> TransformBase:
    """Instantiate the correct TransformBase subclass from a config object."""
    cls = TRANSFORM_REGISTRY[config.op]
    return cls(config)
