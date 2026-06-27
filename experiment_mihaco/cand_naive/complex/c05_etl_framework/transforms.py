"""transforms.py — Transform base class and concrete implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from config import FilterConfig, RenameConfig, DeriveConfig, AggregateConfig


class Transform(ABC):
    """Abstract base class for all transform steps."""

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> None:
        """Raise ValueError if required columns are missing from df."""

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the transform and return the resulting DataFrame."""


class FilterRows(Transform):
    """Keep only rows where column op_kind value is True."""

    _OPS = {
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    def __init__(self, cfg: FilterConfig) -> None:
        self.column = cfg.column
        self.op_kind = cfg.op_kind
        self.value = cfg.value

    def validate(self, df: pd.DataFrame) -> None:
        if self.column not in df.columns:
            raise ValueError(
                f"FilterRows: column {self.column!r} not in DataFrame "
                f"(available: {list(df.columns)})"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        op_func = self._OPS[self.op_kind]
        col = df[self.column]
        # Cast value to float if column is numeric
        value = self.value
        if pd.api.types.is_numeric_dtype(col):
            value = float(value)
        mask = op_func(col, value)
        return df[mask].reset_index(drop=True)


class RenameColumns(Transform):
    """Rename columns according to a mapping dict."""

    def __init__(self, cfg: RenameConfig) -> None:
        self.mapping = cfg.mapping

    def validate(self, df: pd.DataFrame) -> None:
        # Missing keys are silently skipped — no validation needed
        pass

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Only rename keys that exist in the DataFrame
        actual_mapping = {k: v for k, v in self.mapping.items() if k in df.columns}
        return df.rename(columns=actual_mapping)


class DeriveColumn(Transform):
    """Add a new column using df.eval(expr)."""

    def __init__(self, cfg: DeriveConfig) -> None:
        self.column = cfg.column
        self.expr = cfg.expr

    def validate(self, df: pd.DataFrame) -> None:
        # Per spec: derive expr validation is not strictly required;
        # missing column refs would error at eval time
        pass

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df[self.column] = df.eval(self.expr)
        return df


class Aggregate(Transform):
    """Group by columns and aggregate."""

    def __init__(self, cfg: AggregateConfig) -> None:
        self.group_by = cfg.group_by
        self.agg = cfg.agg

    def validate(self, df: pd.DataFrame) -> None:
        missing = []
        for col in self.group_by:
            if col not in df.columns:
                missing.append(col)
        for col in self.agg.keys():
            if col not in df.columns:
                missing.append(col)
        if missing:
            raise ValueError(
                f"Aggregate: columns {missing!r} not in DataFrame "
                f"(available: {list(df.columns)})"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        grouped = df.groupby(self.group_by)
        result = grouped.agg(self.agg).reset_index()
        return result


# Transform registry: maps op name -> factory function taking a config object
TRANSFORM_REGISTRY: dict[str, type[Transform]] = {
    "filter": FilterRows,
    "rename": RenameColumns,
    "derive": DeriveColumn,
    "aggregate": Aggregate,
}


def build_transform(cfg: Any) -> Transform:
    """Build a Transform from a config dataclass."""
    cls = TRANSFORM_REGISTRY.get(cfg.op)
    if cls is None:
        raise ValueError(f"Unknown transform op: {cfg.op!r}")
    return cls(cfg)
