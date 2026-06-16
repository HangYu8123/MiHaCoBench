"""DataFrame construction/validation for c08_pivot_report.

Turns a list of row dicts into a pandas DataFrame, with a guard against empty
input.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def build_frame(records: list[dict]) -> pd.DataFrame:
    """Build a DataFrame from a list of row dicts.

    Parameters
    ----------
    records:
        A list of dictionaries, one per row. Keys become columns.

    Raises
    ------
    ValueError
        If ``records`` is empty.
    """
    if not records:
        raise ValueError("records must be a non-empty list of row dicts")
    return pd.DataFrame.from_records(records)
