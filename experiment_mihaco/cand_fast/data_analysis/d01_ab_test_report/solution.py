"""
A/B Test Report — solution.py

Public contract:
  analyze(df: pandas.DataFrame) -> dict
  main(argv: list[str] | None = None) -> int
"""

import argparse
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")  # Must be called before importing pyplot
import matplotlib.pyplot as plt
import numpy
import pandas
import scipy.stats


def analyze(df: pandas.DataFrame) -> dict:
    """Run a Welch two-sample t-test comparing group B against group A."""
    a_vals = df[df["group"] == "A"]["value"]
    b_vals = df[df["group"] == "B"]["value"]

    mean_A = float(a_vals.mean())
    mean_B = float(b_vals.mean())
    n_A = int(a_vals.count())
    n_B = int(b_vals.count())
    std_A = float(a_vals.std(ddof=1))
    std_B = float(b_vals.std(ddof=1))

    # Welch t-test: B first so positive t means B > A
    result = scipy.stats.ttest_ind(b_vals, a_vals, equal_var=False)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)
    welch_df = float(result.df)

    # Cohen's d: pooled std using sample stds (ddof=1)
    pooled_std = math.sqrt((std_A ** 2 + std_B ** 2) / 2)
    cohens_d = float((mean_B - mean_A) / pooled_std)

    # 95% CI of mean difference (B - A)
    diff = mean_B - mean_A
    se = math.sqrt(std_A ** 2 / n_A + std_B ** 2 / n_B)
    t_crit = float(scipy.stats.t.ppf(0.975, df=welch_df))
    ci95_low = float(diff - t_crit * se)
    ci95_high = float(diff + t_crit * se)

    reject_null = bool(p_value < 0.05)

    return {
        "group_means": {"A": mean_A, "B": mean_B},
        "n": {"A": n_A, "B": n_B},
        "t_stat": t_stat,
        "p_value": p_value,
        "df": welch_df,
        "cohens_d": cohens_d,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": reject_null,
    }


def main(argv: list = None) -> int:
    """CLI entry point."""
    try:
        parser = argparse.ArgumentParser(description="A/B Test Report")
        parser.add_argument("--data", required=True, help="Path to CSV file")
        parser.add_argument("--output-dir", required=True, help="Output directory")
        args = parser.parse_args(argv)

        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        df = pandas.read_csv(args.data)
        results = analyze(df)

        # Write results.json
        results_path = os.path.join(output_dir, "results.json")
        with open(results_path, "w") as f:
            f.write(json.dumps(results))

        a_vals = df[df["group"] == "A"]["value"]
        b_vals = df[df["group"] == "B"]["value"]

        # Plot 1: histograms for groups A and B (two subplots, one figure)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].hist(a_vals, bins=20, color="steelblue", edgecolor="black")
        axes[0].set_title("Group A — Value Distribution")
        axes[0].set_xlabel("Value")
        axes[0].set_ylabel("Frequency")
        axes[1].hist(b_vals, bins=20, color="salmon", edgecolor="black")
        axes[1].set_title("Group B — Value Distribution")
        axes[1].set_xlabel("Value")
        axes[1].set_ylabel("Frequency")
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, "histogram.png"))
        plt.close(fig)

        # Plot 2: boxplot comparing both groups side-by-side
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        ax2.boxplot([a_vals.tolist(), b_vals.tolist()], labels=["A", "B"])
        ax2.set_title("A/B Group Comparison — Boxplot")
        ax2.set_xlabel("Group")
        ax2.set_ylabel("Value")
        fig2.tight_layout()
        fig2.savefig(os.path.join(output_dir, "boxplot.png"))
        plt.close(fig2)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
