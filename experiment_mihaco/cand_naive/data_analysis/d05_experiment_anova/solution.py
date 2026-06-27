"""
solution.py — One-Way ANOVA with Bonferroni Correction
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
from scipy.stats import f_oneway, ttest_ind


def analyze(df: pd.DataFrame) -> dict:
    """Performs one-way ANOVA and pairwise t-tests with Bonferroni correction."""
    groups = ["ctrl", "low", "high"]

    # Compute group means
    group_means = {g: float(df[df["group"] == g]["response"].mean()) for g in groups}

    # One-way ANOVA
    arrays = [df[df["group"] == g]["response"].values for g in groups]
    f_stat, p_val = f_oneway(*arrays)
    anova_F = float(f_stat)
    anova_p = float(p_val)
    significant = anova_p < 0.05

    # Pairwise t-tests with Bonferroni correction (3 comparisons fixed)
    n_comparisons = 3
    pairs = [("ctrl", "low"), ("ctrl", "high"), ("low", "high")]
    significant_pairs = []
    for g1, g2 in pairs:
        a1 = df[df["group"] == g1]["response"].values
        a2 = df[df["group"] == g2]["response"].values
        _, raw_p = ttest_ind(a1, a2)
        corrected_p = min(raw_p * n_comparisons, 1.0)
        if corrected_p < 0.05:
            pair = sorted([g1, g2])
            significant_pairs.append(pair)

    # Sort significant_pairs lexicographically
    significant_pairs.sort(key=lambda x: (x[0], x[1]))

    return {
        "group_means": group_means,
        "anova_F": anova_F,
        "anova_p": anova_p,
        "significant": significant,
        "significant_pairs": significant_pairs,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-Way ANOVA with Bonferroni Correction")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)

    # Read data
    df = pd.read_csv(args.data)

    # Run analysis
    results = analyze(df)

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Write results.json
    results_path = os.path.join(args.output_dir, "results.json")
    with open(results_path, "w") as f:
        json.dump(results, f)

    groups = ["ctrl", "low", "high"]

    # --- Boxplot ---
    fig, ax = plt.subplots()
    data_by_group = [df[df["group"] == g]["response"].values for g in groups]
    ax.boxplot(data_by_group, labels=groups)
    ax.set_xlabel("Group")
    ax.set_ylabel("Response")
    ax.set_title("Response by Group (Boxplot)")
    boxplot_path = os.path.join(args.output_dir, "boxplot.png")
    fig.savefig(boxplot_path)
    plt.close(fig)

    # --- Error-bar chart (mean ± 95% CI) ---
    fig, ax = plt.subplots()
    means = []
    cis = []
    for g in groups:
        vals = df[df["group"] == g]["response"].values
        mean = np.mean(vals)
        std = np.std(vals, ddof=1)
        n = len(vals)
        ci = 1.96 * std / math.sqrt(n)
        means.append(mean)
        cis.append(ci)

    x = np.arange(len(groups))
    ax.errorbar(x, means, yerr=cis, fmt="o", capsize=5)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_xlabel("Group")
    ax.set_ylabel("Mean Response")
    ax.set_title("Mean ± 95% CI by Group")
    errorbar_path = os.path.join(args.output_dir, "errorbar.png")
    fig.savefig(errorbar_path)
    plt.close(fig)

    sys.exit(0)


if __name__ == "__main__":
    main()
