"""transforms.py — Transform base class and concrete transform subclasses.

Deliberately-broken reference for complex/c05_etl_framework.

PLANTED DEFECT: The Aggregate transform applies the aggregation function to the
wrong column. Instead of aggregating the column specified in ``agg``, it always
aggregates the first numeric column in the DataFrame, producing wrong sums.
This causes tests that check aggregate values to fail.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

import pandas as pd

from config import (
    AggregateConfig,
    DeriveConfig,
    FilterConfig,
    RenameConfig,
    TransformConfig,
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TRANSFORM_REGISTRY: dict[str, type["Transform"]] = {}


def _register(op: str) -> Callable[[type], type]:
    """Class decorator that registers a Transform subclass under ``op``."""
    def decorator(cls: type) -> type:
        TRANSFORM_REGISTRY[op] = cls
        return cls
    return decorator


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Transform(ABC):
    """Abstract base for all ETL transforms."""

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this transform to ``df`` and return the result."""

    def validate(self, df: pd.DataFrame) -> None:
        """Raise ``ValueError`` if required columns are missing."""


# ---------------------------------------------------------------------------
# Concrete transforms
# ---------------------------------------------------------------------------

_OP_KIND_MAP: dict[str, Callable[[Any, Any], Any]] = {
    ">":  lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


@_register("filter")
class FilterRows(Transform):
    """Keep only rows where ``column op_kind value`` is True."""

    def __init__(self, cfg: FilterConfig) -> None:
        self._cfg = cfg
        try:
            self._value: Any = float(cfg.value)
        except (TypeError, ValueError):
            self._value = cfg.value

    def validate(self, df: pd.DataFrame) -> None:
        if self._cfg.column not in df.columns:
            raise ValueError(
                f"FilterRows: column {self._cfg.column!r} not found in DataFrame "
                f"(available: {list(df.columns)})"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        op_fn = _OP_KIND_MAP.get(self._cfg.op_kind)
        if op_fn is None:
            raise ValueError(f"FilterRows: unknown op_kind {self._cfg.op_kind!r}")
        col = df[self._cfg.column]
        if isinstance(self._value, float):
            col = pd.to_numeric(col, errors="coerce")
        mask = op_fn(col, self._value)
        return df[mask].reset_index(drop=True)


@_register("rename")
class RenameColumns(Transform):
    """Rename columns according to a mapping dict."""

    def __init__(self, cfg: RenameConfig) -> None:
        self._cfg = cfg

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        existing = {k: v for k, v in self._cfg.mapping.items() if k in df.columns}
        return df.rename(columns=existing)


@_register("derive")
class DeriveColumn(Transform):
    """Add a new column computed by ``df.eval(expr)``."""

    def __init__(self, cfg: DeriveConfig) -> None:
        self._cfg = cfg

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result[self._cfg.column] = df.eval(self._cfg.expr)
        return result


@_register("aggregate")
class Aggregate(Transform):
    """Group-by aggregation transform.

    BUG: aggregates the wrong column — uses the first numeric column instead
    of the column(s) specified in the agg dict. This produces wrong sums.
    """

    def __init__(self, cfg: AggregateConfig) -> None:
        self._cfg = cfg

    def validate(self, df: pd.DataFrame) -> None:
        required = set(self._cfg.group_by) | set(self._cfg.agg.keys())
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Aggregate: columns {sorted(missing)} not found in DataFrame "
                f"(available: {list(df.columns)})"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # BUG: build a wrong agg dict that uses the first non-group column
        # instead of the columns specified in self._cfg.agg
        non_group_cols = [c for c in df.columns if c not in self._cfg.group_by]
        numeric_cols = [c for c in non_group_cols
                        if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            # Fallback: use the correct agg (no bug possible without numerics)
            grouped = df.groupby(self._cfg.group_by, as_index=False)
            return grouped.agg(self._cfg.agg).reset_index(drop=True)
        # Use the first numeric column for all agg functions (wrong!)
        wrong_col = numeric_cols[0]
        wrong_agg = {wrong_col: list(self._cfg.agg.values())[0]}
        grouped = df.groupby(self._cfg.group_by, as_index=False)
        result = grouped.agg(wrong_agg).reset_index(drop=True)
        return result


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_transform(cfg: TransformConfig) -> Transform:
    """Instantiate the correct Transform subclass for ``cfg``."""
    type_name = type(cfg).__name__.lower()
    op_key = type_name.replace("config", "")
    cls = TRANSFORM_REGISTRY.get(op_key)
    if cls is None:
        raise ValueError(f"No transform registered for config type {type(cfg).__name__!r}")
    return cls(cfg)
