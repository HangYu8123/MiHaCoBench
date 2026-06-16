"""transforms.py — Transform base class and subclasses for the ETL framework."""
from __future__ import annotations

import operator
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

# Operator mapping for filter steps
_OP_MAP = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


class Transform(ABC):
    """Abstract base class for all transform steps."""

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this transform to df and return the resulting DataFrame."""
        raise NotImplementedError


class FilterRows(Transform):
    """Keep only rows where column op_kind value is true."""

    def __init__(self, column: str, op_kind: str, value: Any) -> None:
        self.column = column
        self.op_kind = op_kind
        self.value = value

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.column not in df.columns:
            raise ValueError(
                f"FilterRows: column '{self.column}' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )
        op_fn = _OP_MAP.get(self.op_kind)
        if op_fn is None:
            raise ValueError(f"FilterRows: unknown op_kind '{self.op_kind}'")

        # Try to cast value to float for numeric comparison
        try:
            cast_value = float(self.value)
        except (TypeError, ValueError):
            cast_value = self.value

        mask = op_fn(df[self.column], cast_value)
        return df[mask].reset_index(drop=True)


class RenameColumns(Transform):
    """Rename columns according to mapping; missing keys are silently skipped."""

    def __init__(self, mapping: Dict[str, str]) -> None:
        self.mapping = mapping

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.mapping, errors="ignore")


class DeriveColumn(Transform):
    """Add a new column using df.eval(expr)."""

    def __init__(self, column: str, expr: str) -> None:
        self.column = column
        self.expr = expr

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df[self.column] = df.eval(self.expr)
        return df


class Aggregate(Transform):
    """Group by listed columns and aggregate."""

    def __init__(self, group_by: List[str], agg: Dict[str, str]) -> None:
        self.group_by = group_by
        self.agg = agg

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Validate at the time this step is applied
        for col in self.group_by:
            if col not in df.columns:
                raise ValueError(
                    f"Aggregate: group_by column '{col}' not found in DataFrame. "
                    f"Available columns: {list(df.columns)}"
                )
        for col in self.agg:
            if col not in df.columns:
                raise ValueError(
                    f"Aggregate: agg column '{col}' not found in DataFrame. "
                    f"Available columns: {list(df.columns)}"
                )
        return df.groupby(self.group_by).agg(self.agg).reset_index()


# Transform registry mapping op name to class
REGISTRY: Dict[str, type] = {
    "filter": FilterRows,
    "rename": RenameColumns,
    "derive": DeriveColumn,
    "aggregate": Aggregate,
}


def _extract_expr_columns(expr: str) -> List[str]:
    """Extract identifiers from a pandas eval expression (best-effort)."""
    # Find all valid Python identifiers in the expression
    tokens = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', expr)
    # Filter out Python keywords/built-ins that are not column names
    import keyword
    return [t for t in tokens if not keyword.iskeyword(t)]
