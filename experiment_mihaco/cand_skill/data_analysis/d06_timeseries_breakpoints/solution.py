"""
d06_timeseries_breakpoints — Time-Series Changepoint Detection
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind


def analyze(df: pd.DataFrame) -> dict:
    """Detect changepoint and run Welch t-test on a time-series DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Must have at least a ``value`` column (and optionally a ``day`` column).

    Returns
    -------
    dict with keys:
        rolling_mean_last, breakpoint_index, mean_before, mean_after,
        t_stat, p_value, reject_null

    Raises
    ------
    ValueError
        If *df* is empty (zero rows).
    """
    if len(df) == 0:
        raise ValueError("DataFrame must not be empty.")

    # --- 7-day rolling statistics -------------------------------------------
    rolling_mean = df["value"].rolling(window=7, min_periods=1).mean()
    rolling_mean_last = float(rolling_mean.iloc[-1])

    # --- Changepoint detection -----------------------------------------------
    # Search index i in [1, len(df)-1) — half-open, last valid i = len(df)-2
    values = df["value"].to_numpy()
    n = len(values)

    diffs = []
    for i in range(1, n - 1):          # range(1, n-1) gives i in [1, n-2]
        diff = abs(values[:i].mean() - values[i:].mean())
        diffs.append(diff)

    # diffs[k] corresponds to split at i = k + 1
    breakpoint_index = int(np.argmax(diffs)) + 1

    # Recompute means from the stored breakpoint to avoid loop-variable hazards
    mean_before = float(values[:breakpoint_index].mean())
    mean_after = float(values[breakpoint_index:].mean())

    # --- Welch two-sample t-test ---------------------------------------------
    before = values[:breakpoint_index]
    after = values[breakpoint_index:]
    result = ttest_ind(before, after, equal_var=False)
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


def main(argv=None) -> int:
    """CLI entry point.

    Usage
    -----
    python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(
        description="Time-series changepoint detection."
    )
    parser.add_argument("--data", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "--output-dir", required=True, dest="output_dir",
        help="Directory where results.json and series.png are written."
    )
    args = parser.parse_args(argv)

    # Read data
    df = pd.read_csv(args.data)

    # Run analysis
    results = analyze(df)

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON
    json_path = output_dir / "results.json"
    with open(json_path, "w") as f:
        f.write(json.dumps(results))

    # Plot
    bp = results["breakpoint_index"]
    fig, ax = plt.subplots()
    ax.plot(df["day"], df["value"], label="value")
    # Use the actual day value at breakpoint_index for the vertical line
    bp_day = df["day"].iloc[bp]
    ax.axvline(x=bp_day, color="red", linestyle="--", label=f"breakpoint (day {bp_day})")
    ax.set_xlabel("day")
    ax.set_ylabel("value")
    ax.set_title("Time-Series with Detected Changepoint")
    ax.legend()
    fig.savefig(output_dir / "series.png")
    plt.close(fig)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
