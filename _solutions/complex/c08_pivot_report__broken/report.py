"""report — public facade for c08_pivot_report.

BROKEN VARIANT: ``pivot`` omits ``fill_value=0``, so missing ``(index, column)``
combinations come back as ``NaN`` and the resulting columns become float dtype.
This causes the missing-combination / integer-dtype / no-NaN tests to fail,
while present-combination values still match. The module still imports and runs
cleanly — it is a logic bug, not a crash.

The grader imports only from this file::

    from report import Report
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from frame import build_frame

__all__ = ["Report"]

_VALID_AGG = {"sum", "count"}


class Report:
    """Reporting engine over a list of row dicts."""

    def __init__(self, records: list[dict]) -> None:
        self._frame: pd.DataFrame = build_frame(records)

    # ------------------------------------------------------------------ #
    # Pivot
    # ------------------------------------------------------------------ #

    def pivot(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Pivot ``value`` aggregated by ``agg`` over ``index`` x ``columns``.

        Planted defect: ``fill_value=0`` is omitted, so absent combinations
        remain ``NaN`` and the dtype is float — violating the contract.
        """
        if agg not in _VALID_AGG:
            raise ValueError(f"agg must be one of {sorted(_VALID_AGG)}, got {agg!r}")

        table = pd.pivot_table(
            self._frame,
            index=index,
            columns=columns,
            values=value,
            aggfunc=agg,
            # BROKEN: no fill_value -> NaN for missing combos, float dtype.
        )
        return table.sort_index(axis=0).sort_index(axis=1)

    # ------------------------------------------------------------------ #
    # Totals (margins)
    # ------------------------------------------------------------------ #

    def totals(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Pivot plus a ``"Total"`` row and ``"Total"`` column of marginal sums."""
        table = self.pivot(index, columns, value, agg)

        table["Total"] = table.sum(axis=1)
        total_row = table.sum(axis=0)
        total_row.name = "Total"
        table = pd.concat([table, total_row.to_frame().T])
        return table

    # ------------------------------------------------------------------ #
    # Top-N
    # ------------------------------------------------------------------ #

    def top_n(self, index: str, value: str, n: int) -> list[tuple]:
        """Top ``n`` groups by summed ``value`` (total desc, label asc tie-break)."""
        grouped = self._frame.groupby(index)[value].sum()
        pairs = [(label, _as_scalar(total)) for label, total in grouped.items()]
        pairs.sort(key=lambda p: p[0])
        pairs.sort(key=lambda p: p[1], reverse=True)
        return pairs[:n]


def _as_scalar(v: Any) -> Any:
    """Convert a numpy scalar to a native Python scalar where possible."""
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    return v
