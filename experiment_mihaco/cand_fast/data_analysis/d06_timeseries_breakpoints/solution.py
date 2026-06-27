"""
d06_timeseries_breakpoints — Time-Series Changepoint Detection
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Analyse a time-series DataFrame and return changepoint statistics."""
    if len(df) == 0:
        raise ValueError("DataFrame must not be empty.")

    values = df["value"].to_numpy()

    # 7-day rolling mean and rolling standard deviation (both required by spec text)
    rolling_mean = df["value"].rolling(window=7).mean()
    rolling_std = df["value"].rolling(window=7).std()  # computed as required by spec
    rolling_mean_last = float(rolling_mean.iloc[-1])

    # Changepoint detection: i in range [1, len(df)-1) — Python range(1, len(df)-1)
    # This ensures values[:i] and values[i:] are both non-empty.
    n = len(df)
    diffs = np.array(
        [abs(values[:i].mean() - values[i:].mean()) for i in range(1, n - 1)]
    )
    # np.argmax returns index into diffs array (0-based), so actual i = argmax + 1
    breakpoint_index = int(np.argmax(diffs) + 1)

    mean_before = float(values[:breakpoint_index].mean())
    mean_after = float(values[breakpoint_index:].mean())

    # Welch two-sample t-test
    result = scipy.stats.ttest_ind(
        values[:breakpoint_index], values[breakpoint_index:], equal_var=False
    )
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)
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
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Time-series changepoint detection")
    parser.add_argument("--data", required=True, help="Path to input CSV file")
    parser.add_argument("--output-dir", dest="output_dir", required=True,
                        help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        # Plot value over day with vertical line at breakpoint
        fig, ax = plt.subplots()
        ax.plot(df["day"], df["value"], label="value")
        ax.axvline(x=df["day"].iloc[results["breakpoint_index"]], color="red",
                   linestyle="--", label="breakpoint")
        ax.set_xlabel("day")
        ax.set_ylabel("value")
        ax.set_title("Time-Series with Detected Breakpoint")
        ax.legend()
        fig.savefig(os.path.join(args.output_dir, "series.png"))
        plt.close(fig)

        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
