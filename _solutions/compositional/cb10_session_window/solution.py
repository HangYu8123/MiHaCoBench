"""Gold reference for compositional/cb10_session_window.

Group time-ordered events into sessions. Two consecutive events (in
``(ts, id)`` order) belong to the same session iff their timestamp gap is
``<= gap``; a gap STRICTLY GREATER THAN ``gap`` starts a new session.

The whole task turns on that one boundary (``> gap`` vs ``>= gap``): when a gap
equals ``gap`` exactly the events must stay together. Composes pandas (the total
ordering) with numpy (consecutive gaps via ``numpy.diff``).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sessionize(df: pd.DataFrame, gap: float) -> list[dict]:
    """Partition events into sessions under an inclusive ``gap`` threshold.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain an integer ``"id"`` column (unique) and a numeric ``"ts"``
        column. Rows may be in any order.
    gap : float
        Non-negative maximum gap between consecutive events that keeps them in
        the same session. A gap strictly greater than ``gap`` starts a new one.

    Returns
    -------
    list[dict]
        One dict per session, in start order, each with keys
        ``{"ids": list[int], "start_ts", "end_ts", "count": int}``. ``ids`` are
        in ``(ts, id)`` order. Empty list when ``df`` has no rows.
    """
    if gap < 0:
        raise ValueError("gap must be non-negative")
    if "id" not in df.columns:
        raise KeyError("id")
    if "ts" not in df.columns:
        raise KeyError("ts")
    if len(df) == 0:
        return []

    ordered = df.sort_values(["ts", "id"], kind="mergesort").reset_index(drop=True)
    ts = ordered["ts"].to_numpy()
    ids = ordered["id"].tolist()
    ts_list = ordered["ts"].tolist()

    # Consecutive gaps; a new session begins where the gap is STRICTLY > gap.
    diffs = np.diff(ts) if len(ts) > 1 else np.empty(0)

    sessions: list[dict] = []
    cur_ids = [ids[0]]
    cur_start = ts_list[0]
    cur_end = ts_list[0]
    for i in range(1, len(ids)):
        if diffs[i - 1] > gap:
            sessions.append({
                "ids": cur_ids,
                "start_ts": cur_start,
                "end_ts": cur_end,
                "count": len(cur_ids),
            })
            cur_ids = [ids[i]]
            cur_start = ts_list[i]
        else:
            cur_ids.append(ids[i])
        cur_end = ts_list[i]
    sessions.append({
        "ids": cur_ids,
        "start_ts": cur_start,
        "end_ts": cur_end,
        "count": len(cur_ids),
    })
    return sessions
