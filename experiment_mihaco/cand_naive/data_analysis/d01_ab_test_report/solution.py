"""solution.py — A/B Test Report (Data Analysis 01)

Public API
----------
analyze(df)         : Run Welch two-sample t-test and return summary dict.
main(argv=None)     : CLI entry point.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # must come before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import ttest_ind  # surface-form requirement
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Run a Welch two-sample t-test comparing group B against group A.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain columns ``group`` (str, 'A' or 'B') and ``value`` (float).

    Returns
    -------
    dict with keys:
        group_means  : {"A": float, "B": float}  — arithmetic mean per group
        n            : {"A": int,   "B": int}    — sample size per group
        t_stat       : float  — Welch t-statistic (B vs A, positive when B > A)
        p_value      : float  — two-tailed p-value
        df           : float  — Welch–Satterthwaite degrees of freedom
        cohens_d     : float  — Cohen's d using pooled_std = sqrt((s_A^2 + s_B^2)/2)
        ci95_low     : float  — lower bound of 95% CI of mean difference (B − A)
        ci95_high    : float  — upper bound of 95% CI of mean difference (B − A)
        reject_null  : bool   — True iff p_value < 0.05
    """
    a_vals = df.loc[df["group"] == "A", "value"].dropna()
    b_vals = df.loc[df["group"] == "B", "value"].dropna()

    n_a = int(len(a_vals))
    n_b = int(len(b_vals))

    mean_a = float(a_vals.mean())
    mean_b = float(b_vals.mean())

    # Sample standard deviations (ddof=1)
    std_a = float(a_vals.std(ddof=1))
    std_b = float(b_vals.std(ddof=1))

    # Welch t-test: B vs A (positive t_stat means B > A)
    t_stat, p_value = ttest_ind(b_vals, a_vals, equal_var=False)
    t_stat = float(t_stat)
    p_value = float(p_value)

    # Welch–Satterthwaite degrees of freedom
    var_a_n = std_a ** 2 / n_a
    var_b_n = std_b ** 2 / n_b
    welch_df = (var_a_n + var_b_n) ** 2 / (
        (var_a_n ** 2) / (n_a - 1) + (var_b_n ** 2) / (n_b - 1)
    )
    welch_df = float(welch_df)

    # Cohen's d
    pooled_std = math.sqrt((std_a ** 2 + std_b ** 2) / 2)
    cohens_d = float((mean_b - mean_a) / pooled_std)

    # 95% Confidence interval of (mean_B - mean_A)
    diff = mean_b - mean_a
    se = math.sqrt(std_a ** 2 / n_a + std_b ** 2 / n_b)
    t_crit = float(scipy.stats.t.ppf(0.975, df=welch_df))
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


def main(argv: Optional[list] = None) -> int:
    """CLI entry point.

    Usage
    -----
    python solution.py --data <csv_path> --output-dir <dir>

    Reads the CSV, calls analyze(), and writes inside <dir>:
      results.json         — JSON-serialised analysis dict
      histograms.png       — histogram of value per group (two subplots)
      boxplot.png          — boxplot comparing the two groups

    Returns 0 on success, non-zero on error.
    """
    parser = argparse.ArgumentParser(description="A/B Test Report")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
    except Exception as exc:
        print(f"ERROR reading CSV: {exc}", file=sys.stderr)
        return 1

    try:
        results = analyze(df)
    except Exception as exc:
        print(f"ERROR during analysis: {exc}", file=sys.stderr)
        return 1

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Write results.json
    results_path = os.path.join(output_dir, "results.json")
    try:
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f)
    except Exception as exc:
        print(f"ERROR writing results.json: {exc}", file=sys.stderr)
        return 1

    # Prepare group data for plots
    a_vals = df.loc[df["group"] == "A", "value"].dropna()
    b_vals = df.loc[df["group"] == "B", "value"].dropna()

    # Figure 1 — Histograms (two subplots, one per group)
    try:
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].hist(a_vals, bins=30, color="steelblue", edgecolor="white")
        axes[0].set_title("Group A — value distribution")
        axes[0].set_xlabel("value")
        axes[0].set_ylabel("count")

        axes[1].hist(b_vals, bins=30, color="tomato", edgecolor="white")
        axes[1].set_title("Group B — value distribution")
        axes[1].set_xlabel("value")
        axes[1].set_ylabel("count")

        fig.tight_layout()
        hist_path = os.path.join(output_dir, "histograms.png")
        fig.savefig(hist_path, dpi=100)
        plt.close(fig)
    except Exception as exc:
        print(f"ERROR saving histograms: {exc}", file=sys.stderr)
        return 1

    # Figure 2 — Boxplot
    try:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.boxplot(
            [a_vals.tolist(), b_vals.tolist()],
            labels=["A", "B"],
            patch_artist=True,
            boxprops=dict(facecolor="lightblue"),
        )
        ax.set_title("A/B Comparison — Boxplot")
        ax.set_xlabel("group")
        ax.set_ylabel("value")
        boxplot_path = os.path.join(output_dir, "boxplot.png")
        fig.savefig(boxplot_path, dpi=100)
        plt.close(fig)
    except Exception as exc:
        print(f"ERROR saving boxplot: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
