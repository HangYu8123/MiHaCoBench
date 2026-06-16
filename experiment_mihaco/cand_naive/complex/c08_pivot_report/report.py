"""report.py — Facade for the pivot_report task.

Public contract:
    from report import Report
"""

import pandas as pd
import numpy as np

import frame as _frame


class Report:
    """Reporting engine that wraps a pandas DataFrame."""

    def __init__(self, records: list[dict]):
        """Build internal frame from records.

        Raises ValueError if records is empty (propagated from build_frame).
        """
        self._df = _frame.build_frame(records)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def pivot(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return a pivot table with integer cells, NaN filled with 0.

        Parameters
        ----------
        index   : column name to use as row labels
        columns : column name to use as column labels
        value   : column name to aggregate
        agg     : "sum" or "count"
        """
        result = pd.pivot_table(
            self._df,
            values=value,
            index=index,
            columns=columns,
            aggfunc=agg,
            fill_value=0,
        )

        # Ensure integer dtype (fill_value=0 keeps int when possible, but
        # float can sneak in when the source column is float; force it).
        result = result.fillna(0).astype(int)

        # Sort both axes ascending.
        result = result.sort_index(axis=0).sort_index(axis=1)

        # Remove the columns name attribute to produce a clean DataFrame.
        result.columns.name = None
        result.index.name = index

        return result

    def totals(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return the pivot table with "Total" row and column appended."""
        base = self.pivot(index, columns, value, agg)

        # Row marginal sums → "Total" column
        base["Total"] = base.sum(axis=1)

        # Column marginal sums → "Total" row
        total_row = base.sum(axis=0)
        total_row.name = "Total"

        result = pd.concat([base, total_row.to_frame().T])

        # Ensure integer dtype throughout.
        result = result.astype(int)

        return result

    def top_n(self, index: str, value: str, n: int) -> list[tuple]:
        """Return the top-n groups by summed value.

        Parameters
        ----------
        index : column to group by
        value : column to sum
        n     : maximum number of results to return

        Returns
        -------
        List of (index_label, total) tuples sorted by total DESC,
        then index_label ASC on ties.
        """
        grouped = (
            self._df
            .groupby(index, sort=False)[value]
            .sum()
            .reset_index()
        )
        grouped.columns = ["_idx", "_val"]

        # Sort: total descending, then label ascending for ties.
        grouped = grouped.sort_values(
            by=["_val", "_idx"],
            ascending=[False, True],
        )

        return [
            (row["_idx"], int(row["_val"]))
            for _, row in grouped.head(n).iterrows()
        ]
