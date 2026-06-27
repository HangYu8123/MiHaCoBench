"""
Paired Before/After Experiment Report
Data Analysis 07 — d07_paired_design
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
    Returns a dict with analysis results.
    """
    before = df["before"].values
    after = df["after"].values
    diffs = after - before

    n = int(len(df))
    mean_before = float(np.mean(before))
    mean_after = float(np.mean(after))
    mean_diff = float(np.mean(diffs))

    # Paired t-test: scipy.stats.ttest_rel(after, before)
    t_result = scipy.stats.ttest_rel(after, before)
    t_stat = float(t_result.statistic)
    p_value = float(t_result.pvalue)

    # Cohen's d for paired design: mean_diff / std(diffs, ddof=1)
    std_diff = float(np.std(diffs, ddof=1))
    cohens_d = mean_diff / std_diff

    # 95% CI of the mean paired difference
    se = std_diff / math.sqrt(n)
    t_crit = scipy.stats.t.ppf(0.975, df=n - 1)
    ci95_low = mean_diff - t_crit * se
    ci95_high = mean_diff + t_crit * se

    reject_null = bool(p_value < 0.05)

    return {
        "n": n,
        "mean_before": mean_before,
        "mean_after": mean_after,
        "mean_diff": mean_diff,
        "t_stat": t_stat,
        "p_value": p_value,
        "cohens_d": cohens_d,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": reject_null,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Paired before/after experiment analysis")
    parser.add_argument("--data", required=True, help="Path to paired.csv")
    parser.add_argument("--output-dir", required=True, help="Directory to write outputs")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # 1. Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        diffs = df["after"].values - df["before"].values

        # 2. Histogram of paired differences
        fig1, ax1 = plt.subplots()
        ax1.hist(diffs, bins=20, edgecolor="black")
        ax1.set_xlabel("after - before")
        ax1.set_ylabel("Count")
        ax1.set_title("Histogram of Paired Differences (after - before)")
        hist_path = os.path.join(args.output_dir, "histogram_differences.png")
        fig1.savefig(hist_path)
        plt.close(fig1)

        # 3. Before-vs-after paired plot
        fig2, ax2 = plt.subplots()
        for i in range(len(df)):
            ax2.plot([0, 1], [df["before"].iloc[i], df["after"].iloc[i]],
                     color="steelblue", alpha=0.4, linewidth=0.8)
        ax2.set_xticks([0, 1])
        ax2.set_xticklabels(["Before", "After"])
        ax2.set_ylabel("Measurement")
        ax2.set_title("Before vs After (Paired)")
        paired_path = os.path.join(args.output_dir, "before_after_paired.png")
        fig2.savefig(paired_path)
        plt.close(fig2)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
