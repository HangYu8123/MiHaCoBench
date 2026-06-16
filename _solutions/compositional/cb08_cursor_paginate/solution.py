"""Gold reference for compositional/cb08_cursor_paginate.

Stable cursor pagination over a sorted pandas DataFrame.

Composes:
  * pandas  — the input table and the (sort_key ASC, id ASC) ordering,
  * json    — the cursor payload encoding,
  * base64  — the opaque, URL-safe cursor token.

The ordering is total: rows are sorted by (df[sort_key] ASC, df["id"] ASC),
with the integer ``id`` column acting as a stable tie-breaker so two rows with
the same sort_key value can never swap places between calls.

The cursor is EXCLUSIVE: a page returns the first ``page_size`` rows whose
(sort_key, id) is *strictly* lexicographically greater than the cursor's
(sort_key, id). The row that produced the cursor is therefore never repeated.
``cursor=None`` starts at the very beginning. ``next_cursor`` is the token for
the last returned row, or ``None`` when that row is the final row of the whole
ordering (so there is never a trailing empty page).
"""
from __future__ import annotations

import base64
import json

import pandas as pd


def _to_native(value):
    """Coerce a pandas/numpy scalar to a JSON-serialisable native Python value."""
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return value.item()
        except (ValueError, TypeError):  # pragma: no cover - defensive
            return value
    return value


def _encode_cursor(sort_value, row_id: int) -> str:
    """Encode (sort_value, id) into an opaque URL-safe base64(json) token."""
    payload = json.dumps([_to_native(sort_value), int(row_id)], separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(token: str):
    """Decode a cursor token into ``(sort_value, id)``.

    Raises
    ------
    ValueError
        If the token is not valid base64(json) of a ``[sort_value, id]`` pair.
    """
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        decoded = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — normalise every decode failure
        raise ValueError(f"malformed cursor token: {token!r}") from exc
    if not isinstance(decoded, list) or len(decoded) != 2:
        raise ValueError(f"cursor token does not hold a [sort_value, id] pair: {token!r}")
    sort_value, row_id = decoded[0], decoded[1]
    if not isinstance(row_id, int) or isinstance(row_id, bool):
        raise ValueError(f"cursor id must be an integer: {token!r}")
    return sort_value, row_id


def paginate(df: pd.DataFrame, sort_key: str, page_size: int,
             cursor: str | None = None) -> dict:
    """Return one page of ``df`` under stable, exclusive cursor pagination.

    Rows are ordered by ``(df[sort_key] ASC, df["id"] ASC)``; ``id`` is a unique
    integer column that breaks ties on ``sort_key``. A page is the first
    ``page_size`` rows whose ``(sort_key, id)`` is *strictly* greater than the
    cursor's ``(sort_key, id)`` in that order (the cursor is EXCLUSIVE). When
    ``cursor is None`` the page starts at the beginning.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain an integer ``id`` column (unique) and the ``sort_key``
        column.
    sort_key : str
        Name of the primary sort column.
    page_size : int
        Number of rows per page; must be >= 1.
    cursor : str | None
        Opaque base64(json) token of the previous page's last row, or ``None``.

    Returns
    -------
    dict
        ``{"rows": list[dict], "next_cursor": str | None}``. ``rows`` are the
        page rows as record dicts. ``next_cursor`` is the token for the last
        returned row, or ``None`` when that row is the last row of the whole
        ordering (no trailing empty page is ever produced).

    Raises
    ------
    ValueError
        If ``page_size < 1`` or ``cursor`` is malformed/undecodable.
    KeyError
        If the ``id`` column or the ``sort_key`` column is missing.
    """
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")
    if "id" not in df.columns:
        raise KeyError("id")
    if sort_key not in df.columns:
        raise KeyError(sort_key)

    # Total order: sort_key ascending, then id ascending as the stable tie-break.
    ordered = df.sort_values(by=[sort_key, "id"], kind="mergesort").reset_index(drop=True)

    if cursor is None:
        start = 0
    else:
        cur_sort, cur_id = _decode_cursor(cursor)
        # First index strictly after the cursor in (sort_key, id) lexicographic order.
        start = len(ordered)
        for i in range(len(ordered)):
            row_sort = _to_native(ordered.iloc[i][sort_key])
            row_id = int(ordered.iloc[i]["id"])
            if (row_sort, row_id) > (cur_sort, cur_id):
                start = i
                break

    page = ordered.iloc[start:start + page_size]
    rows = page.to_dict(orient="records")

    if len(rows) == 0 or start + page_size >= len(ordered):
        next_cursor = None
    else:
        last = page.iloc[-1]
        next_cursor = _encode_cursor(last[sort_key], int(last["id"]))

    return {"rows": rows, "next_cursor": next_cursor}
