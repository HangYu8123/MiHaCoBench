"""Broken reference for compositional/cb10_session_window.

PLANTED DEFECT (the boundary ambiguity): a new session is started when the gap is
``>= gap`` instead of ``> gap``. So two consecutive events exactly ``gap`` apart —
which the contract says belong to the SAME session — are wrongly split into two.
Every other part (sorting, ordering, output shape, exception paths) is identical,
so only inputs containing an exact-gap boundary reveal the defect.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sessionize(df: pd.DataFrame, gap: float) -> list[dict]:
    """BROKEN: uses ``>= gap`` (inclusive) as the session break instead of ``> gap``."""
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

    diffs = np.diff(ts) if len(ts) > 1 else np.empty(0)

    sessions: list[dict] = []
    cur_ids = [ids[0]]
    cur_start = ts_list[0]
    cur_end = ts_list[0]
    for i in range(1, len(ids)):
        if diffs[i - 1] >= gap:  # BUG: should be strictly greater than gap
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
