import pandas as pd
import numpy as np


def sessionize(df: pd.DataFrame, gap: float) -> list[dict]:
    """Group time-ordered events into sessions using an inclusive gap boundary."""
    if gap < 0:
        raise ValueError("gap must be non-negative")
    if "id" not in df.columns:
        raise KeyError("id")
    if "ts" not in df.columns:
        raise KeyError("ts")

    if len(df) == 0:
        return []

    # Sort by (ts ASC, id ASC) without mutating the original df
    sorted_df = df.sort_values(["ts", "id"]).reset_index(drop=True)

    # Compute consecutive gaps using numpy
    ts_values = sorted_df["ts"].to_numpy()
    gaps = np.diff(ts_values)

    # A new session starts where the gap is strictly greater than `gap`
    # The first event always starts the first session
    new_session = np.concatenate(([True], gaps > gap))

    session_ids = np.cumsum(new_session) - 1  # 0-indexed session labels

    sessions = []
    ids_col = sorted_df["id"].to_numpy()
    ts_col = sorted_df["ts"].to_numpy()

    n_sessions = int(session_ids[-1]) + 1
    for s in range(n_sessions):
        mask = session_ids == s
        event_ids = ids_col[mask].tolist()
        event_ts = ts_col[mask]
        sessions.append({
            "ids": event_ids,
            "start_ts": event_ts[0],
            "end_ts": event_ts[-1],
            "count": int(np.sum(mask)),
        })

    return sessions
