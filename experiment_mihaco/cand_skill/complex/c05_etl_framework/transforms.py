"""transforms.py — Transform base class + 4 subclasses + registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from config import FilterConfig, RenameConfig, DeriveConfig, AggregateConfig


class Transform(ABC):
    """Abstract base class for all pipeline transforms."""

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this transform to df and return the result."""
        ...


class FilterRows(Transform):
    """Keep rows where column op_kind value is True."""

    OP_MAP = {
        ">": "__gt__",
        ">=": "__ge__",
        "<": "__lt__",
        "<=": "__le__",
        "==": "__eq__",
        "!=": "__ne__",
    }

    def __init__(self, config: FilterConfig) -> None:
        self.column = config.column
        self.op_kind = config.op_kind
        self.value: Any = config.value

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        col = df[self.column]
        value = self.value

        # Cast to float when the value is numeric
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = float(value)

        method = self.OP_MAP.get(self.op_kind)
        if method is None:
            raise ValueError(f"Unknown op_kind: {self.op_kind!r}")

        mask = getattr(col, method)(value)
        return df[mask].reset_index(drop=True)


class RenameColumns(Transform):
    """Rename columns per mapping; silently skip missing source keys."""

    def __init__(self, config: RenameConfig) -> None:
        self.mapping = config.mapping

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Only rename keys that actually exist
        actual = {k: v for k, v in self.mapping.items() if k in df.columns}
        return df.rename(columns=actual)


class DeriveColumn(Transform):
    """Add a new column using df.eval(expr)."""

    def __init__(self, config: DeriveConfig) -> None:
        self.column = config.column
        self.expr = config.expr

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df[self.column] = df.eval(self.expr)
        return df


class Aggregate(Transform):
    """Group by specified columns and aggregate."""

    def __init__(self, config: AggregateConfig) -> None:
        self.group_by = config.group_by
        self.agg = config.agg

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.groupby(self.group_by).agg(self.agg).reset_index()
        return result


# Registry mapping op name to class
TRANSFORM_REGISTRY = {
    "filter": FilterRows,
    "rename": RenameColumns,
    "derive": DeriveColumn,
    "aggregate": Aggregate,
}
