"""frame.py — DataFrame builder for pivot_report task."""

import pandas as pd


def build_frame(records: list[dict]) -> pd.DataFrame:
    """Build and return a DataFrame from a list of row dicts.

    Raises ValueError if records is empty.
    """
    if not records:
        raise ValueError("records must not be empty")
    return pd.DataFrame(records)
