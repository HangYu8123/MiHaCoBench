import base64
import json

import pandas


def paginate(df: pandas.DataFrame, sort_key: str, page_size: int, cursor: str | None = None) -> dict:
    """Stable cursor-based pagination over a sorted DataFrame.

    Returns one page of rows strictly after the cursor position in
    (sort_key ASC, id ASC) order, along with the next cursor token.
    """
    # --- Input validation (KeyError checks: "id" first, then sort_key) ---
    if "id" not in df.columns:
        raise KeyError("id")
    if sort_key not in df.columns:
        raise KeyError(sort_key)
    if page_size < 1:
        raise ValueError("page_size must be >= 1")

    # --- Sort (do not mutate df) ---
    sorted_df = df.sort_values([sort_key, "id"], ascending=True)

    # --- Decode cursor ---
    if cursor is not None:
        try:
            payload = json.loads(base64.b64decode(cursor))
        except Exception as exc:
            raise ValueError("malformed cursor token") from exc
        if not (isinstance(payload, list) and len(payload) == 2):
            raise ValueError("cursor payload must be a 2-element JSON array")
        sort_val, id_val = payload[0], payload[1]

        # Filter rows strictly after the cursor position
        mask = (sorted_df[sort_key] > sort_val) | (
            (sorted_df[sort_key] == sort_val) & (sorted_df["id"] > id_val)
        )
        filtered = sorted_df[mask]
    else:
        filtered = sorted_df

    # --- Slice page ---
    page = filtered.iloc[:page_size]

    # --- Handle empty page ---
    if len(page) == 0:
        return {"rows": [], "next_cursor": None}

    # --- Determine next_cursor ---
    # "No trailing empty page": next_cursor is None iff the page's last row
    # is the last row of the entire ordering.
    # Equivalently: if filtered has no more rows beyond this page, next_cursor = None.
    if len(filtered) <= page_size:
        next_cursor = None
    else:
        last_row = page.iloc[-1]
        token_payload = [last_row[sort_key], int(last_row["id"])]
        next_cursor = base64.b64encode(json.dumps(token_payload).encode()).decode()

    return {"rows": page.to_dict(orient="records"), "next_cursor": next_cursor}
