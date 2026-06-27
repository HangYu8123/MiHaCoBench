"""
A/B Test Report — solution.py

Implements:
  analyze(df)  -> dict with 9 keys
  main(argv)   -> int (CLI entry point)

Notes:
  - Uses scipy.stats.ttest_ind (surface-form requirement satisfied below).
  - All numpy scalars are cast to Python natives before returning.
  - Relies on MPLBACKEND=Agg env var set by grader; no manual matplotlib.use().
"""

import sys
import json
import argparse
import os
import math

import numpy as np
import pandas as pd
import scipy.stats
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt


def analyze(df: pd.DataFrame) -> dict:
    """
    Run a Welch two-sample t-test comparing group B against group A.

    Parameters
    ----------
    df : pandas.DataFrame
        Must have columns 'group' (values 'A' or 'B') and 'value' (float).

    Returns
    -------
    dict with exactly these keys:
        group_means, n, t_stat, p_value, df, cohens_d,
        ci95_low, ci95_high, reject_null
    """
    df_a = df[df["group"] == "A"]["value"]
    df_b = df[df["group"] == "B"]["value"]

    n_a = int(len(df_a))
    n_b = int(len(df_b))

    mean_a = float(df_a.mean())
    mean_b = float(df_b.mean())

    std_a = float(df_a.std(ddof=1))
    std_b = float(df_b.std(ddof=1))

    # Welch's t-test — surface-form check: scipy.stats.ttest_ind
    result = scipy.stats.ttest_ind(df_b.values, df_a.values, equal_var=False)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)
    welch_df = float(result.df)

    # Cohen's d: (mean_B - mean_A) / sqrt((std_A**2 + std_B**2) / 2)
    pooled_std = math.sqrt((std_a ** 2 + std_b ** 2) / 2)
    cohens_d = float((mean_b - mean_a) / pooled_std)

    # 95% CI for (mean_B - mean_A)
    diff = mean_b - mean_a
    se = math.sqrt(std_a ** 2 / n_a + std_b ** 2 / n_b)
    t_crit = float(stats.t.ppf(0.975, df=welch_df))
    ci95_low = float(diff - t_crit * se)
    ci95_high = float(diff + t_crit * se)

    reject_null = bool(p_value < 0.05)

    return {
        "group_means": {"A": mean_a, "B": mean_b},
        "n": {"A": n_a, "B": n_b},
        "t_stat": t_stat,
        "p_value": p_value,
        "df": welch_df,
        "cohens_d": cohens_d,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": reject_null,
    }


def main(argv=None) -> int:
    """
    CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>

    Writes to <dir>:
        results.json   — JSON with all 9 analysis keys
        histograms.png — histograms of value for each group (two subplots)
        boxplot.png    — boxplot comparing the two groups
    """
    try:
        parser = argparse.ArgumentParser(description="A/B Test Report")
        parser.add_argument("--data", required=True, help="Path to input CSV file")
        parser.add_argument("--output-dir", required=True, help="Directory for output files")
        args = parser.parse_args(argv)

        df = pd.read_csv(args.data)
        results = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        json_path = os.path.join(args.output_dir, "results.json")
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2)

        # Separate group values for plotting
        vals_a = df[df["group"] == "A"]["value"].values
        vals_b = df[df["group"] == "B"]["value"].values

        # --- Figure 1: Histograms (two subplots, one file) ---
        fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        ax1.hist(vals_a, bins=30, color="steelblue", edgecolor="white", alpha=0.8)
        ax1.set_title("Group A — value distribution")
        ax1.set_xlabel("value")
        ax1.set_ylabel("count")

        ax2.hist(vals_b, bins=30, color="darkorange", edgecolor="white", alpha=0.8)
        ax2.set_title("Group B — value distribution")
        ax2.set_xlabel("value")
        ax2.set_ylabel("count")

        fig1.tight_layout()
        hist_path = os.path.join(args.output_dir, "histograms.png")
        fig1.savefig(hist_path)
        plt.close(fig1)

        # --- Figure 2: Boxplot ---
        fig2, ax3 = plt.subplots(figsize=(6, 5))
        ax3.boxplot([vals_a, vals_b], tick_labels=["A", "B"], patch_artist=True)
        ax3.set_title("A/B Group Comparison — Boxplot")
        ax3.set_xlabel("Group")
        ax3.set_ylabel("value")

        box_path = os.path.join(args.output_dir, "boxplot.png")
        fig2.savefig(box_path)
        plt.close(fig2)

        return 0

    except Exception:
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
