"""report.py — FACADE: class Report (imports build_frame from frame.py)."""

import pandas as pd
import numpy as np

import frame


class Report:
    """Reporting engine built on top of pandas pivot tables."""

    def __init__(self, records: list[dict]):
        """Build the internal frame via frame.build_frame(records).

        Raises ValueError if records is empty.
        """
        self._df = frame.build_frame(records)

    def pivot(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return a pivot table of value aggregated by agg over index x columns.

        - agg is either "sum" or "count".
        - Missing (index, column) combinations are filled with 0 (integer).
        - All cells are integer dtype (no floats, no NaN).
        - Columns are sorted ascending; index is sorted ascending.
        """
        result = pd.pivot_table(
            self._df,
            values=value,
            index=index,
            columns=columns,
            aggfunc=agg,
            fill_value=0,
        )
        # Sort index and columns ascending
        result = result.sort_index(axis=0).sort_index(axis=1)
        # Ensure integer dtype (fill_value=0 may still produce float if any NaN
        # was present before filling)
        result = result.astype(int)
        # Remove the columns name label that pivot_table sets
        result.columns.name = columns
        result.index.name = index
        return result

    def totals(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return pivot table plus row/column marginal sums labelled "Total".

        - Extra row "Total": column-wise sums of the pivot data.
        - Extra column "Total": row-wise sums of the pivot data.
        - Bottom-right cell ("Total", "Total") is the grand total.
        """
        base = self.pivot(index, columns, value, agg)

        # Compute row totals (sum across columns for each index row)
        row_totals = base.sum(axis=1).astype(int)

        # Compute column totals (sum down rows for each column)
        col_totals = base.sum(axis=0).astype(int)

        # Grand total
        grand_total = int(col_totals.sum())

        # Add "Total" column to base
        result = base.copy()
        result["Total"] = row_totals

        # Build the "Total" row: col_totals + grand total
        total_row = col_totals.to_frame().T
        total_row.index = ["Total"]
        total_row["Total"] = grand_total

        # Concatenate
        result = pd.concat([result, total_row])

        # Ensure integer dtype throughout
        result = result.astype(int)

        return result

    def top_n(self, index: str, value: str, n: int) -> list[tuple]:
        """Return top n groups by summed value, descending; ties broken by label ascending.

        Returns list of (index_label, total) tuples, at most n items.
        """
        grouped = self._df.groupby(index)[value].sum()
        # Sort: primary by value descending, secondary by label ascending
        # pandas sort_values is stable; sort by index ascending first, then by value descending
        grouped = grouped.sort_index(ascending=True)
        grouped = grouped.sort_values(ascending=False, kind="mergesort")
        top = grouped.head(n)
        return [(label, int(total)) for label, total in top.items()]
