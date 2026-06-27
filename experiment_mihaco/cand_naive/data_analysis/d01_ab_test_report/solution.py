"""
solution.py — A/B Test Analysis

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
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import ttest_ind


def analyze(df: pd.DataFrame) -> dict:
    """Run a Welch two-sample t-test comparing group B against group A."""
    a_vals = df[df["group"] == "A"]["value"].values
    b_vals = df[df["group"] == "B"]["value"].values

    mean_a = float(np.mean(a_vals))
    mean_b = float(np.mean(b_vals))
    n_a = int(len(a_vals))
    n_b = int(len(b_vals))

    std_a = float(np.std(a_vals, ddof=1))
    std_b = float(np.std(b_vals, ddof=1))

    # Welch t-test: B vs A (B - A orientation)
    t_stat, p_value = ttest_ind(b_vals, a_vals, equal_var=False)
    t_stat = float(t_stat)
    p_value = float(p_value)

    # Welch-Satterthwaite degrees of freedom
    var_a = std_a ** 2
    var_b = std_b ** 2
    welch_df = (var_a / n_a + var_b / n_b) ** 2 / (
        (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    )
    welch_df = float(welch_df)

    # Cohen's d
    pooled_std = math.sqrt((var_a + var_b) / 2)
    cohens_d = float((mean_b - mean_a) / pooled_std)

    # 95% CI of mean difference (B - A)
    diff = mean_b - mean_a
    se = math.sqrt(var_a / n_a + var_b / n_b)
    t_crit = float(stats.t.ppf(0.975, df=welch_df))
    ci95_low = float(diff - t_crit * se)
    ci95_high = float(diff + t_crit * se)

    return {
        "group_means": {"A": mean_a, "B": mean_b},
        "n": {"A": n_a, "B": n_b},
        "t_stat": t_stat,
        "p_value": p_value,
        "df": welch_df,
        "cohens_d": cohens_d,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": bool(p_value < 0.05),
    }


def main(argv: list = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="A/B Test Analysis")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Write results.json
        with open(os.path.join(output_dir, "results.json"), "w") as f:
            json.dump(results, f)

        a_vals = df[df["group"] == "A"]["value"].values
        b_vals = df[df["group"] == "B"]["value"].values

        # Histogram figure with two subplots (one per group)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].hist(a_vals, bins=30, color="steelblue", edgecolor="white")
        axes[0].set_title("Group A — Value Distribution")
        axes[0].set_xlabel("Value")
        axes[0].set_ylabel("Count")

        axes[1].hist(b_vals, bins=30, color="salmon", edgecolor="white")
        axes[1].set_title("Group B — Value Distribution")
        axes[1].set_xlabel("Value")
        axes[1].set_ylabel("Count")

        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, "histograms.png"))
        plt.close(fig)

        # Boxplot figure
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        ax2.boxplot([a_vals, b_vals], labels=["A", "B"])
        ax2.set_title("Group A vs Group B — Boxplot")
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
