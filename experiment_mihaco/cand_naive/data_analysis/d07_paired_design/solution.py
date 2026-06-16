"""
Paired Before/After Experiment Report
Data Analysis Task d07_paired_design
"""

import argparse
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """
    Run a paired t-test comparing after against before.
    Returns a dict with statistical results.
    """
    before = df["before"].values
    after = df["after"].values

    n = len(df)
    mean_before = float(np.mean(before))
    mean_after = float(np.mean(after))

    diffs = after - before
    mean_diff = float(np.mean(diffs))

    # Paired t-test using ttest_rel
    t_result = scipy.stats.ttest_rel(after, before)
    t_stat = float(t_result.statistic)
    p_value = float(t_result.pvalue)

    # Cohen's d for paired design
    std_diff = float(np.std(diffs, ddof=1))
    cohens_d = mean_diff / std_diff

    # 95% CI for mean paired difference
    se = std_diff / math.sqrt(n)
    t_crit = scipy.stats.t.ppf(0.975, df=n - 1)
    ci95_low = mean_diff - t_crit * se
    ci95_high = mean_diff + t_crit * se

    reject_null = p_value < 0.05

    return {
        "n": int(n),
        "mean_before": mean_before,
        "mean_after": mean_after,
        "mean_diff": mean_diff,
        "t_stat": t_stat,
        "p_value": p_value,
        "cohens_d": float(cohens_d),
        "ci95_low": float(ci95_low),
        "ci95_high": float(ci95_high),
        "reject_null": bool(reject_null),
    }


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point.
    Usage: python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(description="Paired before/after experiment analysis")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory to write outputs")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        diffs = df["after"].values - df["before"].values

        # Plot 1: Histogram of paired differences
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        ax1.hist(diffs, bins=20, edgecolor="black", alpha=0.7)
        ax1.axvline(x=0, color="red", linestyle="--", linewidth=1.5, label="No change")
        ax1.axvline(x=float(np.mean(diffs)), color="blue", linestyle="-",
                    linewidth=1.5, label=f"Mean diff = {np.mean(diffs):.3f}")
        ax1.set_xlabel("Paired Difference (after - before)")
        ax1.set_ylabel("Frequency")
        ax1.set_title("Histogram of Paired Differences (After - Before)")
        ax1.legend()
        fig1.tight_layout()
        hist_path = os.path.join(output_dir, "histogram_diffs.png")
        fig1.savefig(hist_path)
        plt.close(fig1)

        # Plot 2: Before-vs-after paired plot
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        before_vals = df["before"].values
        after_vals = df["after"].values
        subject_ids = range(len(df))

        for i in subject_ids:
            ax2.plot([0, 1], [before_vals[i], after_vals[i]],
                     color="gray", alpha=0.4, linewidth=0.8)

        ax2.plot([0] * len(df), before_vals, "o", color="steelblue",
                 label="Before", markersize=4, alpha=0.6)
        ax2.plot([1] * len(df), after_vals, "o", color="tomato",
                 label="After", markersize=4, alpha=0.6)

        # Plot mean values
        ax2.plot([0, 1], [np.mean(before_vals), np.mean(after_vals)],
                 "D-", color="black", linewidth=2.5, markersize=8, label="Mean")

        ax2.set_xticks([0, 1])
        ax2.set_xticklabels(["Before", "After"])
        ax2.set_ylabel("Measurement")
        ax2.set_title("Before vs After Paired Measurements")
        ax2.legend()
        fig2.tight_layout()
        paired_path = os.path.join(output_dir, "paired_plot.png")
        fig2.savefig(paired_path)
        plt.close(fig2)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
