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
    """Perform one-way ANOVA and pairwise t-tests with Bonferroni correction."""
    groups = ["ctrl", "low", "high"]

    # Compute group means (cast to plain float)
    group_means = {g: float(df[df["group"] == g]["response"].mean()) for g in groups}

    # One-way ANOVA
    arrays = [df[df["group"] == g]["response"].values for g in groups]
    anova_result = scipy.stats.f_oneway(*arrays)
    anova_F = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)

    significant = bool(anova_p < 0.05)

    # Pairwise t-tests with Bonferroni correction (3 comparisons)
    pairs = [("ctrl", "low"), ("ctrl", "high"), ("low", "high")]
    significant_pairs = []
    for g1, g2 in pairs:
        a = df[df["group"] == g1]["response"].values
        b = df[df["group"] == g2]["response"].values
        ttest_result = scipy.stats.ttest_ind(a, b)
        raw_p = float(ttest_result.pvalue)
        corrected_p = min(raw_p * 3, 1.0)
        if corrected_p < 0.05:
            # Each pair as a sorted list of group names
            pair = sorted([g1, g2])
            significant_pairs.append(pair)

    # Sort the outer list lexicographically (by first element, then second)
    significant_pairs.sort()

    return {
        "group_means": group_means,
        "anova_F": anova_F,
        "anova_p": anova_p,
        "significant": significant,
        "significant_pairs": significant_pairs,
    }


def main(argv: list[str] | None = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="One-way ANOVA with Bonferroni correction.")
    parser.add_argument("--data", required=True, help="Path to input CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    # Read data
    df = pd.read_csv(args.data)

    # Run analysis
    results = analyze(df)

    # Write results.json
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "results.json"), "w") as f:
        json.dump(results, f)

    # Prepare group data in a consistent order for plots
    plot_groups = ["ctrl", "high", "low"]
    group_data = [df[df["group"] == g]["response"].values for g in plot_groups]

    # --- Boxplot ---
    fig, ax = plt.subplots()
    ax.boxplot(group_data, labels=plot_groups)
    ax.set_xlabel("Group")
    ax.set_ylabel("Response")
    ax.set_title("Response by Group (Box Plot)")
    plt.savefig(os.path.join(output_dir, "boxplot.png"))
    plt.close()

    # --- Errorbar plot ---
    fig, ax = plt.subplots()
    x_positions = list(range(len(plot_groups)))
    means = []
    cis = []
    for vals in group_data:
        n = len(vals)
        mean = float(np.mean(vals))
        std = float(np.std(vals, ddof=1))  # sample std (ddof=1)
        ci = 1.96 * std / math.sqrt(n)
        means.append(mean)
        cis.append(ci)

    ax.errorbar(x_positions, means, yerr=cis, fmt="o", capsize=5)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(plot_groups)
    ax.set_xlabel("Group")
    ax.set_ylabel("Mean Response")
    ax.set_title("Mean ± 95% CI by Group")
    plt.savefig(os.path.join(output_dir, "errorbar.png"))
    plt.close()

    sys.exit(0)


if __name__ == "__main__":
    main()
