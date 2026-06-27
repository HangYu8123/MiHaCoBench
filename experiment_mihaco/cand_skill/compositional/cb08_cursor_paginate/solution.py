import base64
import json
import pandas


def paginate(df: pandas.DataFrame, sort_key: str, page_size: int, cursor: str | None = None) -> dict:
    """Return one page of df under stable cursor pagination.

    Parameters
    ----------
    df : pandas.DataFrame
        The source table. Must have columns "id" and sort_key.
    sort_key : str
        Column name to sort by (ascending). Ties broken by "id" (ascending).
    page_size : int
        Number of rows per page. Must be >= 1.
    cursor : str | None
        Opaque base64(json([sort_val, id])) token returned by a prior call,
        or None to start from the beginning.

    Returns
    -------
    dict with keys:
        "rows"        : list[dict]  — page rows as record dicts, in (sort_key, id) order
        "next_cursor" : str | None  — token for the last returned row, or None when
                                      the last row of the full ordering has been returned
    """
    # --- Validate page_size first (before column checks) ---
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")

    # --- Validate required columns ---
    if "id" not in df.columns:
        raise KeyError("DataFrame must have an 'id' column")
    if sort_key not in df.columns:
        raise KeyError(f"sort_key column '{sort_key}' not found in DataFrame")

    # --- Build total order (pure — does not mutate df) ---
    sorted_df = df.sort_values(
        by=[sort_key, "id"],
        ascending=[True, True],
    ).reset_index(drop=True)

    # --- Decode cursor ---
    after_key = None
    after_id = None
    if cursor is not None:
        try:
            decoded_bytes = base64.b64decode(cursor)
            decoded = json.loads(decoded_bytes)
            if not isinstance(decoded, list) or len(decoded) != 2:
                raise ValueError("Cursor payload must be a 2-element list")
            after_key, after_id = decoded[0], decoded[1]
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Malformed cursor token: {exc}") from exc
        except Exception as exc:
            raise ValueError(f"Malformed cursor token: {exc}") from exc

    # --- Apply exclusive filter ---
    if after_key is None:
        # Start from the beginning
        candidates = sorted_df
    else:
        # Keep rows strictly after (after_key, after_id) in (sort_key, id) order
        mask = (sorted_df[sort_key] > after_key) | (
            (sorted_df[sort_key] == after_key) & (sorted_df["id"] > after_id)
        )
        candidates = sorted_df[mask]

    # --- Slice the page ---
    page = candidates.iloc[:page_size]

    # --- Handle empty page ---
    if len(page) == 0:
        return {"rows": [], "next_cursor": None}

    # --- Convert to records ---
    rows = page.to_dict(orient="records")

    # --- Determine next_cursor ---
    # next_cursor is None if and only if the last row of the page is the last
    # row of the full sorted order (no trailing empty page rule).
    last_page_sort_val = page.iloc[-1][sort_key]
    last_page_id = page.iloc[-1]["id"]
    last_overall_sort_val = sorted_df.iloc[-1][sort_key]
    last_overall_id = sorted_df.iloc[-1]["id"]

    if last_page_sort_val == last_overall_sort_val and last_page_id == last_overall_id:
        next_cursor = None
    else:
        # Encode [sort_val, id] as base64(json([...]))
        # Convert numpy scalars to native Python types for JSON serialization
        def _to_native(val):
            """Convert numpy scalar to a JSON-serializable Python native type."""
            if hasattr(val, "item"):
                return val.item()
            return val

        payload = json.dumps([_to_native(last_page_sort_val), _to_native(last_page_id)])
        next_cursor = base64.b64encode(payload.encode()).decode()

    return {"rows": rows, "next_cursor": next_cursor}
