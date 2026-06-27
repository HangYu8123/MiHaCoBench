import pandas as pd
import frame as _frame


class Report:
    """Reporting engine backed by a pandas DataFrame."""

    def __init__(self, records: list[dict]):
        # Raises ValueError if records is empty (via build_frame).
        self._df = _frame.build_frame(records)

    def pivot(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return a pivot table aggregated by agg ("sum" or "count").

        - Missing (index, column) combinations are filled with 0 (integer).
        - Every cell is an integer (no floats, no NaN).
        - Rows and columns are sorted ascending.
        """
        result = pd.pivot_table(
            self._df,
            values=value,
            index=index,
            columns=columns,
            aggfunc=agg,
            fill_value=0,
        )
        # Explicit sort on both axes (pivot_table usually sorts but spec mandates it).
        result = result.sort_index(axis=0).sort_index(axis=1)
        # Cast to int — pivot_table can produce float64 even with fill_value=0.
        result = result.astype(int)
        return result

    def totals(self, index: str, columns: str, value: str, agg: str) -> pd.DataFrame:
        """Return the pivot table with a "Total" row and a "Total" column.

        The "Total" row holds column marginal sums; the "Total" column holds
        row marginal sums. The bottom-right ("Total", "Total") cell is the
        grand total. All margin cells are integers.
        """
        df = self.pivot(index, columns, value, agg)
        # Row marginals: sum across columns for each index label.
        df["Total"] = df.sum(axis=1)
        # Column marginals (including the new "Total" column) as a new "Total" row.
        df.loc["Total"] = df.sum(axis=0)
        # Ensure all values remain integers (appending a row can upcast to float).
        df = df.astype(int)
        return df

    def top_n(self, index: str, value: str, n: int) -> list[tuple]:
        """Return top-n groups by summed value as (index_label, total) tuples.

        Ties broken by index_label ascending.
        Returns at most n tuples (fewer if there are fewer than n groups).
        """
        grouped = (
            self._df.groupby(index)[value]
            .sum()
            .reset_index()
        )
        # Sort: total descending, then index label ascending for tie-breaking.
        grouped = grouped.sort_values(
            by=[value, index],
            ascending=[False, True],
        )
        top = grouped.head(n)
        # Convert to list of tuples; cast total to plain int to satisfy strict type checks.
        return [(row[index], int(row[value])) for _, row in top.iterrows()]
