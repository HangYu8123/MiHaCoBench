"""
d06_timeseries_breakpoints — Time-Series Changepoint Detection
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def analyze(df: pd.DataFrame) -> dict:
    """Perform rolling statistics, changepoint detection, and Welch t-test.

    Parameters
    ----------
    df : pandas.DataFrame
        Must have columns 'day' (int) and 'value' (float). Must be non-empty.

    Returns
    -------
    dict with keys: rolling_mean_last, breakpoint_index, mean_before,
    mean_after, t_stat, p_value, reject_null.

    Raises
    ------
    ValueError if df is empty (zero rows).
    """
    if len(df) == 0:
        raise ValueError("DataFrame must not be empty.")

    values = df["value"].to_numpy()
    n = len(values)

    # --- 7-day rolling statistics ---
    rolling = df["value"].rolling(window=7)
    rolling_mean_last = float(rolling.mean().iloc[-1])

    # --- Changepoint detection ---
    # Find index i in [1, n-1) that maximises abs(mean(values[:i]) - mean(values[i:]))
    best_i = 1
    best_score = -1.0

    # Efficient O(n) scan using cumulative sums
    cum_sum = np.cumsum(values)

    for i in range(1, n - 1):
        mean_left = cum_sum[i - 1] / i
        mean_right = (cum_sum[-1] - cum_sum[i - 1]) / (n - i)
        score = abs(mean_left - mean_right)
        if score > best_score:
            best_score = score
            best_i = i

    breakpoint_index = int(best_i)
    mean_before = float(np.mean(values[:breakpoint_index]))
    mean_after = float(np.mean(values[breakpoint_index:]))

    # --- Welch t-test ---
    before = values[:breakpoint_index]
    after = values[breakpoint_index:]
    t_stat, p_value = ttest_ind(before, after, equal_var=False)
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


def main(argv=None) -> int:
    """CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(description="Time-series changepoint detection")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            f.write(json.dumps(results))

        # Write series.png
        fig, ax = plt.subplots()
        ax.plot(df["day"], df["value"], label="value")
        ax.axvline(
            x=df["day"].iloc[results["breakpoint_index"]],
            color="red",
            linestyle="--",
            label=f"breakpoint (index={results['breakpoint_index']})",
        )
        ax.set_xlabel("day")
        ax.set_ylabel("value")
        ax.set_title("Time Series with Detected Changepoint")
        ax.legend()
        png_path = os.path.join(args.output_dir, "series.png")
        fig.savefig(png_path)
        plt.close(fig)

        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
