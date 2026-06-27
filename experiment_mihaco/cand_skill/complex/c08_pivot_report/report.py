"""report.py — FACADE: class Report (imports build_frame from frame.py)."""

import pandas as pd

from frame import build_frame


class Report:
    """Reporting engine backed by a pandas DataFrame."""

    def __init__(self, records: list[dict]) -> None:
        """Build internal frame from records.

        Raises ValueError if records is empty (propagated from build_frame).
        """
        self._df = build_frame(records)

    def pivot(
        self,
        index: str,
        columns: str,
        value: str,
        agg: str,
    ) -> pd.DataFrame:
        """Return a pivot table of value aggregated by agg over index x columns.

        - Every missing (index, column) combination is filled with 0 (integer).
        - All cells are integer dtype (no floats, no NaN).
        - Result columns and index are sorted ascending.
        """
        # Get all unique values for index and columns to enforce full Cartesian product.
        all_index_vals = sorted(self._df[index].unique())
        all_col_vals = sorted(self._df[columns].unique())

        result = pd.pivot_table(
            self._df,
            values=value,
            index=index,
            columns=columns,
            aggfunc=agg,
            fill_value=0,
        )

        # Reindex to full Cartesian product to handle missing combinations
        # (especially important for aggfunc="count" which may drop missing keys).
        result = result.reindex(
            index=all_index_vals,
            columns=all_col_vals,
            fill_value=0,
        )

        # Ensure integer dtype — pivot_table may return float when NaN was present.
        result = result.astype(int)

        # Sort both axes ascending.
        result = result.sort_index(axis=0).sort_index(axis=1)

        # Remove the column axis label for a clean frame.
        result.columns.name = None

        return result

    def totals(
        self,
        index: str,
        columns: str,
        value: str,
        agg: str,
    ) -> pd.DataFrame:
        """Return the pivot table with a 'Total' row and 'Total' column.

        - 'Total' row: column marginal sums.
        - 'Total' column: row marginal sums.
        - ('Total', 'Total') cell is the grand total.
        - All cells are integer dtype.
        """
        base = self.pivot(index, columns, value, agg)

        # Compute grand total from the base pivot (before adding any margins).
        grand_total = int(base.values.sum())

        # Compute column sums (to become the 'Total' row) from the base pivot.
        col_sums = base.sum(axis=0).astype(int)

        # Compute row sums (to become the 'Total' column) from the base pivot.
        row_sums = base.sum(axis=1).astype(int)

        # Append the 'Total' column to the base pivot.
        result = base.copy()
        result["Total"] = row_sums

        # Build the 'Total' row: column sums + grand total in the 'Total' column.
        total_row = col_sums.copy()
        total_row["Total"] = grand_total

        # Append the 'Total' row.
        result.loc["Total"] = total_row

        # Cast everything to int to handle any float upcast during concat/assignment.
        result = result.astype(int)

        return result

    def top_n(self, index: str, value: str, n: int) -> list[tuple]:
        """Return the top n groups by sum of value, sorted desc by total then asc by label.

        Returns a list of (index_label, total) tuples, at most n items.
        """
        grouped = self._df.groupby(index)[value].sum()

        # Sort: descending total, ascending label for tiebreak.
        # Cast label to str for tiebreak comparison to avoid TypeError with mixed types.
        pairs = sorted(
            grouped.items(),
            key=lambda x: (-x[1], str(x[0])),
        )

        return [(label, int(total)) for label, total in pairs[:n]]
