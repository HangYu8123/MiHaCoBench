"""report.py — FACADE: class Report."""

import sys
import os

# Ensure frame.py in the same directory can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from frame import build_frame


class Report:
    """A reporting engine for pivot tables and top-n summaries."""

    def __init__(self, records: list):
        """Build internal frame from records.

        Raises ValueError if records is empty.
        """
        self._df = build_frame(records)

    def pivot(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return a pivot table aggregated by agg ('sum' or 'count').

        - Missing (index, column) combinations are filled with 0 (integer).
        - All cells are integer dtype.
        - Both index and columns are sorted in ascending order.
        """
        result = pd.pivot_table(
            self._df,
            values=value,
            index=index,
            columns=columns,
            aggfunc=agg,
            fill_value=0,
        )
        # Remove the name on the columns axis (pivot_table sets it to the column param)
        result.columns.name = None
        result.index.name = None

        # Ensure integer dtype (pivot_table may return float64)
        result = result.astype(int)

        # Sort both axes ascending
        result = result.sort_index(axis=0).sort_index(axis=1)

        return result

    def totals(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return pivot table with 'Total' row and 'Total' column margins.

        - Extra row labelled 'Total' holds column marginal sums.
        - Extra column labelled 'Total' holds row marginal sums.
        - Bottom-right ('Total', 'Total') cell is the grand total.
        - All cells are integer dtype.
        """
        df = self.pivot(index, columns, value, agg)

        # Add row marginal (sum across columns for each row)
        df["Total"] = df.sum(axis=1).astype(int)

        # Add column marginal (sum across rows for each column, including Total col)
        total_row = df.sum(axis=0).astype(int)
        df.loc["Total"] = total_row

        # Ensure all values are integer dtype
        df = df.astype(int)

        return df

    def top_n(self, index: str, value: str, n: int) -> list:
        """Return the top n groups by summed value as (index_label, total) tuples.

        - Groups are sorted by total DESCENDING; ties broken by index_label ASCENDING.
        - Returns at most n tuples.
        """
        grouped = self._df.groupby(index)[value].sum().reset_index()
        grouped.columns = [index, value]

        # Sort by value descending, then index ascending for tie-breaking
        grouped = grouped.sort_values(
            by=[value, index], ascending=[False, True]
        ).head(n)

        result = []
        for _, row in grouped.iterrows():
            label = row[index]
            total = int(row[value])
            result.append((label, total))

        return result
