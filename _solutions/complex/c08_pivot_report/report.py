"""report — public facade for c08_pivot_report.

Exposes the :class:`Report` class, which wraps a pandas DataFrame (built via
``frame.build_frame``) and offers pivot / margin-total / top-N reporting.

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
    """Reporting engine over a list of row dicts.

    Parameters
    ----------
    records:
        A non-empty list of row dicts. An empty list raises ``ValueError``
        (propagated from :func:`frame.build_frame`).
    """

    def __init__(self, records: list[dict]) -> None:
        self._frame: pd.DataFrame = build_frame(records)

    # ------------------------------------------------------------------ #
    # Pivot
    # ------------------------------------------------------------------ #

    def pivot(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Pivot ``value`` aggregated by ``agg`` over ``index`` x ``columns``.

        Missing ``(index, column)`` combinations are filled with the integer
        ``0`` (never ``NaN``); every cell is an integer. Columns and index are
        sorted ascending.
        """
        if agg not in _VALID_AGG:
            raise ValueError(f"agg must be one of {sorted(_VALID_AGG)}, got {agg!r}")

        table = pd.pivot_table(
            self._frame,
            index=index,
            columns=columns,
            values=value,
            aggfunc=agg,
            fill_value=0,
        )
        # Sort axes ascending and force an integer dtype (no NaN can remain
        # because fill_value=0 already filled the absent combinations).
        table = table.sort_index(axis=0).sort_index(axis=1)
        return table.astype(np.int64)

    # ------------------------------------------------------------------ #
    # Totals (margins)
    # ------------------------------------------------------------------ #

    def totals(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Pivot plus a ``"Total"`` row and ``"Total"`` column of marginal sums.

        The bottom-right ``("Total", "Total")`` cell is the grand total. The
        margin label is the exact string ``"Total"`` (not pandas' default
        ``"All"``).
        """
        table = self.pivot(index, columns, value, agg)

        # Row marginal (sum across columns) -> new "Total" column.
        table["Total"] = table.sum(axis=1)
        # Column marginal (sum down rows, including the new Total column) -> new
        # "Total" row.
        total_row = table.sum(axis=0)
        total_row.name = "Total"
        table = pd.concat([table, total_row.to_frame().T])
        return table.astype(np.int64)

    # ------------------------------------------------------------------ #
    # Top-N
    # ------------------------------------------------------------------ #

    def top_n(self, index: str, value: str, n: int) -> list[tuple]:
        """Top ``n`` groups by summed ``value``.

        Returns ``(index_label, total)`` tuples sorted by total descending,
        ties broken by index label ascending. At most ``n`` tuples.
        """
        grouped = self._frame.groupby(index)[value].sum()
        # Build (label, total) pairs and sort: total descending, then label
        # ascending. Sorting by ascending label first then by descending total
        # with a stable sort yields the required tie-break.
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
