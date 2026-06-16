import base64
import json
import pandas


def paginate(df: pandas.DataFrame, sort_key: str, page_size: int, cursor: str | None = None) -> dict:
    """
    Return one page of df under stable cursor pagination.

    Ordering: rows are ordered by (df[sort_key] ASC, df["id"] ASC).
    The cursor is exclusive: a page returns the first page_size rows strictly
    after the cursor position.

    Args:
        df: pandas DataFrame to paginate
        sort_key: column name to sort by (ascending)
        page_size: number of rows per page (must be >= 1)
        cursor: opaque base64-encoded cursor token, or None to start from beginning

    Returns:
        dict with keys:
            - rows: list of row dicts in (sort_key, id) order
            - next_cursor: opaque token for the last returned row, or None if last row reached

    Raises:
        ValueError: if cursor is malformed or page_size < 1
        KeyError: if "id" or sort_key column is missing from df
    """
    # Validate page_size
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")

    # Validate required columns (raises KeyError if missing)
    if "id" not in df.columns:
        raise KeyError("'id' column is missing from df")
    if sort_key not in df.columns:
        raise KeyError(f"'{sort_key}' column is missing from df")

    # Sort the dataframe by (sort_key ASC, id ASC)
    sorted_df = df.sort_values(by=[sort_key, "id"], ascending=[True, True], kind="stable")

    # Parse cursor if provided
    cursor_sort_val = None
    cursor_id = None
    if cursor is not None:
        try:
            decoded = base64.b64decode(cursor)
            payload = json.loads(decoded)
            if not isinstance(payload, list) or len(payload) != 2:
                raise ValueError("Cursor payload must be a JSON array of [sort_value, id]")
            cursor_sort_val, cursor_id = payload[0], payload[1]
        except (Exception,) as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Malformed cursor token: {e}") from e

    # Filter rows that come strictly after the cursor
    if cursor is None:
        # Start from beginning
        page_df = sorted_df
    else:
        # Find rows where (sort_key, id) > (cursor_sort_val, cursor_id) lexicographically
        sort_vals = sorted_df[sort_key]
        id_vals = sorted_df["id"]

        # Row is after cursor if:
        # sort_val > cursor_sort_val, OR
        # sort_val == cursor_sort_val AND id > cursor_id
        mask = (sort_vals > cursor_sort_val) | (
            (sort_vals == cursor_sort_val) & (id_vals > cursor_id)
        )
        page_df = sorted_df[mask]

    # Take first page_size rows
    page_rows = page_df.head(page_size)

    # Convert to list of dicts
    rows = page_rows.to_dict(orient="records")

    # Determine next_cursor
    next_cursor = None
    if len(rows) > 0:
        last_row = page_rows.iloc[-1]
        last_sort_val = last_row[sort_key]
        last_id = last_row["id"]

        # Check if this is the last row in the full ordering
        # Count rows strictly after the last returned row
        all_sort_vals = sorted_df[sort_key]
        all_id_vals = sorted_df["id"]

        after_mask = (all_sort_vals > last_sort_val) | (
            (all_sort_vals == last_sort_val) & (all_id_vals > last_id)
        )
        rows_after = sorted_df[after_mask]

        if len(rows_after) > 0:
            # There are more rows after; encode the cursor for the last returned row
            payload = [last_sort_val, last_id]
            token_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            next_cursor = base64.b64encode(token_bytes).decode('ascii')
        # else: next_cursor remains None (last row reached, no trailing empty page)

    return {
        "rows": rows,
        "next_cursor": next_cursor,
    }
