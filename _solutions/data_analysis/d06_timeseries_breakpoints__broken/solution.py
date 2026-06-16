"""BROKEN reference for data_analysis/d06_timeseries_breakpoints.

Planted defects (localized):
  1. rolling_mean_last uses the GLOBAL mean instead of the 7-day rolling mean.
  2. breakpoint_index is detected as argmax(values) instead of maximising
     abs(mean_before - mean_after) — this gives a wrong index.

Everything else (ttest_ind, mean_before/mean_after given the broken index,
reject_null, CLI structure) stays intact so only specific grader checks fail.
"""
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

    BUG 1: rolling_mean_last uses the global mean, not a rolling mean.
    BUG 2: breakpoint_index is argmax(values), not the mean-difference maximiser.
    """
    if df.empty:
        raise ValueError("analyze() received an empty DataFrame")

    values = df["value"].to_numpy(dtype=float)
    n = len(values)

    # --- (1) 7-day rolling mean (BROKEN: uses global mean instead) -----------
    # BUG: should be df["value"].rolling(window=7).mean().iloc[-1]
    rolling_mean_last = float(np.mean(values))  # BROKEN: global mean, not rolling

    # Keep rolling in source so surface-form check still finds it
    _roll = df["value"].rolling(window=7)  # noqa: F841

    # --- (2) Changepoint detection (BROKEN: argmax instead of mean-diff) -----
    # BUG: should find index maximising abs(mean_before - mean_after)
    breakpoint_index = int(np.argmax(values))  # BROKEN: wrong criterion

    before = values[:breakpoint_index]
    after = values[breakpoint_index:]

    # Guard against degenerate split (argmax could give index 0 or n-1)
    if len(before) == 0 or len(after) == 0:
        # fallback to midpoint so ttest doesn't crash
        breakpoint_index = n // 2
        before = values[:breakpoint_index]
        after = values[breakpoint_index:]

    mean_before = float(np.mean(before))
    mean_after = float(np.mean(after))

    # --- (3) Welch t-test (correct) ------------------------------------------
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

    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

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
