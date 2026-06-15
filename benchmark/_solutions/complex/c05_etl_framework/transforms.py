"""transforms.py — Transform base class and concrete transform subclasses.

Each transform is registered in a global ``TRANSFORM_REGISTRY`` keyed by its
``op`` string so new transforms can be added without modifying the pipeline.
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
    """Abstract base for all ETL transforms.

    Concrete subclasses must implement :meth:`apply` which receives a DataFrame
    and returns a (possibly new) DataFrame.
    """

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this transform to ``df`` and return the result."""

    def validate(self, df: pd.DataFrame) -> None:
        """Raise ``ValueError`` if required columns are missing.

        The default implementation does nothing. Subclasses override this
        to check that their required columns exist before ``apply`` is called.
        """


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
    """Keep only rows where ``column op_kind value`` is True.

    Numeric ``value`` entries are cast to float for comparison.
    """

    def __init__(self, cfg: FilterConfig) -> None:
        self._cfg = cfg
        # Try to convert value to float for numeric comparisons
        try:
            self._value: Any = float(cfg.value)
        except (TypeError, ValueError):
            self._value = cfg.value

    def validate(self, df: pd.DataFrame) -> None:
        """Raise ValueError if the filter column is missing."""
        if self._cfg.column not in df.columns:
            raise ValueError(
                f"FilterRows: column {self._cfg.column!r} not found in DataFrame "
                f"(available: {list(df.columns)})"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return rows satisfying the filter predicate."""
        op_fn = _OP_KIND_MAP.get(self._cfg.op_kind)
        if op_fn is None:
            raise ValueError(f"FilterRows: unknown op_kind {self._cfg.op_kind!r}")
        col = df[self._cfg.column]
        # Cast column to float when comparing against a float value
        if isinstance(self._value, float):
            col = pd.to_numeric(col, errors="coerce")
        mask = op_fn(col, self._value)
        return df[mask].reset_index(drop=True)


@_register("rename")
class RenameColumns(Transform):
    """Rename columns according to a mapping dict.

    Keys absent from the DataFrame are silently skipped.
    """

    def __init__(self, cfg: RenameConfig) -> None:
        self._cfg = cfg

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return df with columns renamed per mapping."""
        # Only rename keys that actually exist
        existing = {k: v for k, v in self._cfg.mapping.items() if k in df.columns}
        return df.rename(columns=existing)


@_register("derive")
class DeriveColumn(Transform):
    """Add a new column computed by ``df.eval(expr)``."""

    def __init__(self, cfg: DeriveConfig) -> None:
        self._cfg = cfg

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return df with the new derived column added."""
        result = df.copy()
        result[self._cfg.column] = df.eval(self._cfg.expr)
        return result


@_register("aggregate")
class Aggregate(Transform):
    """Group-by aggregation transform.

    After aggregation the result contains only the ``group_by`` columns plus
    the aggregated columns. Index is reset.
    """

    def __init__(self, cfg: AggregateConfig) -> None:
        self._cfg = cfg

    def validate(self, df: pd.DataFrame) -> None:
        """Raise ValueError if any required column is missing."""
        required = set(self._cfg.group_by) | set(self._cfg.agg.keys())
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Aggregate: columns {sorted(missing)} not found in DataFrame "
                f"(available: {list(df.columns)})"
            )

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return the aggregated DataFrame."""
        grouped = df.groupby(self._cfg.group_by, as_index=False)
        return grouped.agg(self._cfg.agg).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_transform(cfg: TransformConfig) -> Transform:
    """Instantiate the correct :class:`Transform` subclass for ``cfg``.

    Looks up the class in :data:`TRANSFORM_REGISTRY` using the lowercase class
    name prefix (e.g. ``FilterConfig`` → ``"filter"``).
    """
    type_name = type(cfg).__name__.lower()
    # Strip trailing "config" suffix: "filterconfig" → "filter"
    op_key = type_name.replace("config", "")
    cls = TRANSFORM_REGISTRY.get(op_key)
    if cls is None:
        raise ValueError(f"No transform registered for config type {type(cfg).__name__!r}")
    return cls(cfg)
