"""transforms.py — Transform base class and concrete transform implementations."""

from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from typing import Callable

import pandas as pd

from config import (
    FilterConfig,
    RenameConfig,
    DeriveConfig,
    AggregateConfig,
    TransformConfig,
)


class Transform(ABC):
    """Abstract base class for all transforms."""

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the transform to a DataFrame and return the result."""
        ...


class FilterRows(Transform):
    """Filter rows based on a column comparison."""

    _OPERATORS: dict[str, Callable] = {
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, config: FilterConfig) -> None:
        self.config = config

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        col = self.config.column
        if col not in df.columns:
            raise ValueError(
                f"FilterRows: column {col!r} not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )
        op_fn = self._OPERATORS[self.config.op_kind]
        value = self.config.value
        # Cast to float for numeric comparison if the column is numeric
        try:
            value = float(value)
        except (TypeError, ValueError):
            pass
        mask = op_fn(df[col], value)
        return df[mask].reset_index(drop=True)


class RenameColumns(Transform):
    """Rename columns according to a mapping."""

    def __init__(self, config: RenameConfig) -> None:
        self.config = config

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Only rename keys that exist in the DataFrame; silently skip the rest
        existing = {k: v for k, v in self.config.mapping.items() if k in df.columns}
        return df.rename(columns=existing)


class DeriveColumn(Transform):
    """Add a new column using df.eval(expr)."""

    def __init__(self, config: DeriveConfig) -> None:
        self.config = config

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result[self.config.column] = df.eval(self.config.expr)
        return result


class Aggregate(Transform):
    """Group by columns and aggregate."""

    def __init__(self, config: AggregateConfig) -> None:
        self.config = config

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        group_by = self.config.group_by
        agg = self.config.agg

        # Validate columns
        for col in group_by:
            if col not in df.columns:
                raise ValueError(
                    f"Aggregate: group_by column {col!r} not found in DataFrame. "
                    f"Available columns: {list(df.columns)}"
                )
        for col in agg:
            if col not in df.columns:
                raise ValueError(
                    f"Aggregate: agg column {col!r} not found in DataFrame. "
                    f"Available columns: {list(df.columns)}"
                )

        result = df.groupby(group_by, as_index=False).agg(agg)
        return result.reset_index(drop=True)


# Transform registry: maps op name → (config class, transform class)
TRANSFORM_REGISTRY: dict[str, type[Transform]] = {
    "filter": FilterRows,
    "rename": RenameColumns,
    "derive": DeriveColumn,
    "aggregate": Aggregate,
}

# Config class → transform class mapping for building transforms from configs
_CONFIG_TO_TRANSFORM: dict[type, type[Transform]] = {
    FilterConfig: FilterRows,
    RenameConfig: RenameColumns,
    DeriveConfig: DeriveColumn,
    AggregateConfig: Aggregate,
}


def build_transform(config: TransformConfig) -> Transform:
    """Build a Transform instance from a config dataclass."""
    transform_cls = _CONFIG_TO_TRANSFORM.get(type(config))
    if transform_cls is None:
        raise ValueError(f"No transform registered for config type {type(config)!r}")
    return transform_cls(config)
