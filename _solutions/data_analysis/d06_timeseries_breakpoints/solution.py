"""Gold reference for data_analysis/d06_timeseries_breakpoints — time-series changepoint detection."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Detect a single level-shift changepoint in a univariate time series.

    Parameters
    ----------
    df:
        DataFrame with columns 'day' (int) and 'value' (float).
        Must be non-empty; raises ValueError otherwise.

    Returns
    -------
    dict with keys:
        rolling_mean_last  : float  – rolling-7-day mean at the last row
        breakpoint_index   : int    – index maximising |mean_before - mean_after|
        mean_before        : float  – mean of values before the breakpoint
        mean_after         : float  – mean of values at/after the breakpoint
        t_stat             : float  – Welch t-test statistic
        p_value            : float  – two-tailed p-value
        reject_null        : bool   – True iff p_value < 0.05
    """
    if df.empty:
        raise ValueError("analyze() received an empty DataFrame")

    values = df["value"].to_numpy(dtype=float)
    n = len(values)

    # --- (1) 7-day rolling mean & std (pandas rolling) -----------------------
    roll = df["value"].rolling(window=7)
    rolling_mean = roll.mean()
    # rolling std is computed but not returned as a top-level key per spec
    _rolling_std = roll.std()  # noqa: F841 (kept to satisfy surface-form rolling usage)
    rolling_mean_last = float(rolling_mean.iloc[-1])

    # --- (2) Changepoint detection -------------------------------------------
    # Maximise abs(mean(values[:i]) - mean(values[i:])) for i in [1, n-1)
    # Using cumulative sums for O(n) computation
    cum = np.cumsum(values)
    total_sum = cum[-1]

    best_diff = -1.0
    best_i = 1
    for i in range(1, n - 1):
        mean_left = cum[i - 1] / i
        mean_right = (total_sum - cum[i - 1]) / (n - i)
        diff = abs(mean_left - mean_right)
        if diff > best_diff:
            best_diff = diff
            best_i = i

    breakpoint_index = int(best_i)
    before = values[:breakpoint_index]
    after = values[breakpoint_index:]
    mean_before = float(np.mean(before))
    mean_after = float(np.mean(after))

    # --- (3) Welch t-test (scipy.stats.ttest_ind) ----------------------------
    t_stat, p_value = scipy.stats.ttest_ind(before, after, equal_var=False)
    t_stat = float(t_stat)
    p_value = float(p_value)
    reject_null = bool(p_value < 0.05)

    return {
        "rolling_mean_last": rolling_mean_last,
        "breakpoint_index": breakpoint_index,
        "mean_before": mean_before,
        "mean_after": mean_after,
        "t_stat": t_stat,
        "p_value": p_value,
        "reject_null": reject_null,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python solution.py --data <csv> --output-dir <dir>."""
    parser = argparse.ArgumentParser(description="Time-series changepoint detection")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write results.json
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    # Plot: line plot of value over day with vertical breakpoint marker
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["day"], df["value"], color="steelblue", linewidth=1.2, label="value")
    ax.axvline(
        x=df["day"].iloc[results["breakpoint_index"]],
        color="red",
        linewidth=1.5,
        linestyle="--",
        label=f"breakpoint (day {results['breakpoint_index']})",
    )
    ax.set_xlabel("day")
    ax.set_ylabel("value")
    ax.set_title("Time-Series with Detected Changepoint")
    ax.legend()
    fig.tight_layout()
    fig.savefig(str(out_dir / "series.png"), dpi=80)
    plt.close(fig)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
