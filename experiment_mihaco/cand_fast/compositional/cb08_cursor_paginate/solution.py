import base64
import json
import pandas as pd


def paginate(df: pd.DataFrame, sort_key: str, page_size: int, cursor: str | None = None) -> dict:
    """
    Return one page of df under stable cursor pagination.

    Ordering: (df[sort_key] ASC, df["id"] ASC)
    The cursor is EXCLUSIVE: returns rows strictly after cursor position.
    No trailing empty page: next_cursor is None when page ends on final row.
    """
    # Validate page_size before any DataFrame access
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")

    # Validate required columns
    if "id" not in df.columns:
        raise KeyError("'id' column is missing from df")
    if sort_key not in df.columns:
        raise KeyError(f"sort_key column '{sort_key}' is missing from df")

    # Sort a copy (never mutate df)
    sorted_df = df.sort_values(by=[sort_key, "id"], ascending=[True, True])

    # Decode cursor if provided
    if cursor is not None:
        try:
            decoded_bytes = base64.b64decode(cursor.encode("ascii"))
            cursor_data = json.loads(decoded_bytes)
            if not isinstance(cursor_data, list) or len(cursor_data) != 2:
                raise ValueError("Cursor payload must be a 2-element array")
            sv, cid = cursor_data
        except (Exception,) as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Malformed cursor token: {e}") from e

        # Apply exclusive keyset filter: (sort_key, id) > (sv, cid)
        mask = (sorted_df[sort_key] > sv) | (
            (sorted_df[sort_key] == sv) & (sorted_df["id"] > cid)
        )
        filtered_df = sorted_df.loc[mask]
    else:
        filtered_df = sorted_df

    # Take page
    page = filtered_df.iloc[:page_size]

    # If page is empty, return immediately
    if len(page) == 0:
        return {"rows": [], "next_cursor": None}

    # Determine next_cursor
    # Check if the last row of the page is the last row of the entire sorted order
    last_page_row = page.iloc[-1]
    last_sorted_row = sorted_df.iloc[-1]

    # Compare by id (which is unique) to determine if we're at the end
    if last_page_row["id"] == last_sorted_row["id"]:
        next_cursor = None
    else:
        # Encode cursor from last row of page
        last_sort_val = last_page_row[sort_key]
        last_id = last_page_row["id"]

        # Convert to native Python types for JSON serialization
        if hasattr(last_sort_val, "item"):
            last_sort_val = last_sort_val.item()
        else:
            last_sort_val = type(last_sort_val)(last_sort_val)

        if hasattr(last_id, "item"):
            last_id = last_id.item()
        else:
            last_id = int(last_id)

        token_payload = json.dumps([last_sort_val, last_id])
        next_cursor = base64.b64encode(token_payload.encode("ascii")).decode("ascii")

    return {
        "rows": page.to_dict(orient="records"),
        "next_cursor": next_cursor,
    }
