"""BROKEN reference for compositional/cb08_cursor_paginate.

PLANTED DEFECT (localized): the cursor is treated as INCLUSIVE instead of
EXCLUSIVE. The boundary uses ``>=`` on the (sort_key, id) pair, so the row that
produced the cursor is selected again at the head of the next page and is
DUPLICATED across the two consecutive pages.

Consequences:
  * a full walk via repeated calls repeats the boundary row of every page,
  * a tie block straddling a page boundary has its boundary row duplicated.

Everything that does not touch the boundary still works: the first page
(cursor=None), single-page results, and all exception paths are unaffected.
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
    """Return one page of ``df`` under cursor pagination (see TASK.md).

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
        ``{"rows": list[dict], "next_cursor": str | None}``.

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

    ordered = df.sort_values(by=[sort_key, "id"], kind="mergesort").reset_index(drop=True)

    if cursor is None:
        start = 0
    else:
        cur_sort, cur_id = _decode_cursor(cursor)
        start = len(ordered)
        for i in range(len(ordered)):
            row_sort = _to_native(ordered.iloc[i][sort_key])
            row_id = int(ordered.iloc[i]["id"])
            # BUG: inclusive boundary (>=) — re-includes the cursor row itself,
            # duplicating it at the head of the next page.
            if (row_sort, row_id) >= (cur_sort, cur_id):
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
