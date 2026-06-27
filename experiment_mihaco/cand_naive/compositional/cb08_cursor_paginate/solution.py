"""
Compositional 08 — cursor_paginate
Stable cursor-based (keyset) pagination over a sorted pandas DataFrame.
"""

import base64
import json
import pandas


def paginate(df: pandas.DataFrame, sort_key: str, page_size: int, cursor: str | None = None) -> dict:
    """
    Return one page of df under stable cursor pagination.

    Ordering: (df[sort_key] ASC, df["id"] ASC).
    Cursor is exclusive — the first page_size rows strictly after the cursor position.

    Returns a dict with:
      - "rows": list of record dicts in (sort_key, id) order
      - "next_cursor": opaque base64 token of last returned row, or None if last row reached
    """
    # Validate page_size
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")

    # Validate required columns
    if "id" not in df.columns:
        raise KeyError("'id' column is missing from df")
    if sort_key not in df.columns:
        raise KeyError(f"sort_key column '{sort_key}' is missing from df")

    # Sort the dataframe by (sort_key ASC, id ASC) — do not mutate original
    sorted_df = df.sort_values(by=[sort_key, "id"], ascending=[True, True], kind="mergesort").reset_index(drop=True)

    if cursor is None:
        # Start from the beginning
        start_idx = 0
    else:
        # Decode the cursor token
        try:
            decoded_bytes = base64.b64decode(cursor)
            payload = json.loads(decoded_bytes.decode("utf-8"))
            if not (isinstance(payload, list) and len(payload) == 2):
                raise ValueError("Cursor payload must be a JSON array of [sort_value, id]")
            cursor_sort_val, cursor_id = payload[0], payload[1]
        except (Exception,) as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Malformed cursor token: {e}") from e

        # Find the first row strictly after (cursor_sort_val, cursor_id)
        # "Strictly after" in (sort_key, id) lexicographic order:
        #   row[sort_key] > cursor_sort_val
        #   OR (row[sort_key] == cursor_sort_val AND row["id"] > cursor_id)
        col = sorted_df[sort_key]
        id_col = sorted_df["id"]

        after_mask = (col > cursor_sort_val) | ((col == cursor_sort_val) & (id_col > cursor_id))

        # Find index of first True in after_mask
        true_indices = after_mask[after_mask].index
        if len(true_indices) == 0:
            # Nothing after cursor — return empty page
            return {"rows": [], "next_cursor": None}
        start_idx = true_indices[0]

    # Slice page_size rows starting from start_idx
    page_df = sorted_df.iloc[start_idx: start_idx + page_size]

    rows = page_df.to_dict(orient="records")

    if len(rows) == 0:
        return {"rows": [], "next_cursor": None}

    # Determine next_cursor
    # next_cursor is None if the last row of the page is the last row of the whole ordering
    last_row = page_df.iloc[-1]
    last_global_idx = start_idx + len(rows) - 1
    total_rows = len(sorted_df)

    if last_global_idx >= total_rows - 1:
        # The last returned row is the final row — no trailing empty page
        next_cursor = None
    else:
        # Encode cursor as base64(json([sort_val, id]))
        sort_val = last_row[sort_key]
        row_id = last_row["id"]

        # Handle numpy/pandas scalar types for JSON serialization
        if hasattr(sort_val, "item"):
            sort_val = sort_val.item()
        if hasattr(row_id, "item"):
            row_id = row_id.item()

        payload = json.dumps([sort_val, row_id], separators=(",", ":"))
        next_cursor = base64.b64encode(payload.encode("utf-8")).decode("ascii")

    return {"rows": rows, "next_cursor": next_cursor}
