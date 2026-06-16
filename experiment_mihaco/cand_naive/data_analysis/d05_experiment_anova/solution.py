"""
Data Analysis 05 — experiment_anova: One-Way ANOVA with Bonferroni Correction
"""

import argparse
import json
import math
import os
import sys
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind


def analyze(df: pd.DataFrame) -> dict:
    """
    Performs a one-way ANOVA and pairwise t-tests with Bonferroni correction.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'group' (categorical) and 'response' (float).

    Returns
    -------
    dict with keys:
        group_means      : dict[str, float]
        anova_F          : float
        anova_p          : float
        significant      : bool
        significant_pairs: list[list[str]]
    """
    # Compute group means
    group_means = {}
    for grp, sub in df.groupby("group"):
        group_means[str(grp)] = float(sub["response"].mean())

    # Extract data per group
    groups = sorted(df["group"].unique())
    data_by_group = {str(g): df.loc[df["group"] == g, "response"].values for g in groups}

    # One-way ANOVA
    arrays = [data_by_group[str(g)] for g in groups]
    F_stat, p_val = f_oneway(*arrays)
    anova_F = float(F_stat)
    anova_p = float(p_val)
    significant = bool(anova_p < 0.05)

    # Pairwise t-tests with Bonferroni correction
    # Fixed pairs: (ctrl, low), (ctrl, high), (low, high)
    pair_names = [("ctrl", "low"), ("ctrl", "high"), ("low", "high")]
    n_comparisons = 3

    significant_pairs = []
    for g1, g2 in pair_names:
        arr1 = data_by_group.get(g1)
        arr2 = data_by_group.get(g2)
        if arr1 is None or arr2 is None:
            continue
        _, raw_p = ttest_ind(arr1, arr2)
        corrected_p = min(float(raw_p) * n_comparisons, 1.0)
        if corrected_p < 0.05:
            # Sort alphabetically
            pair = sorted([g1, g2])
            significant_pairs.append(pair)

    # Sort the list lexicographically
    significant_pairs.sort(key=lambda x: (x[0], x[1]))

    return {
        "group_means": group_means,
        "anova_F": anova_F,
        "anova_p": anova_p,
        "significant": significant,
        "significant_pairs": significant_pairs,
    }


def main(argv: Optional[list] = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="One-Way ANOVA with Bonferroni Correction"
    )
    parser.add_argument("--data", required=True, help="Path to input CSV file")
    parser.add_argument(
        "--output-dir", required=True, help="Directory to write output files"
    )
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

    # Determine group order for plots
    groups = sorted(df["group"].unique())
    data_by_group = {str(g): df.loc[df["group"] == g, "response"].values for g in groups}
    group_labels = [str(g) for g in groups]

    # --- Box plot ---
    fig, ax = plt.subplots()
    plot_data = [data_by_group[g] for g in group_labels]
    ax.boxplot(plot_data, labels=group_labels)
    ax.set_xlabel("Group")
    ax.set_ylabel("Response")
    ax.set_title("Box Plot by Group")
    boxplot_path = os.path.join(args.output_dir, "boxplot.png")
    fig.savefig(boxplot_path)
    plt.close(fig)

    # --- Error bar plot (mean ± 95% CI) ---
    means = []
    cis = []
    for g in group_labels:
        arr = data_by_group[g]
        n = len(arr)
        m = float(np.mean(arr))
        s = float(np.std(arr, ddof=1))
        ci = 1.96 * s / math.sqrt(n)
        means.append(m)
        cis.append(ci)

    fig, ax = plt.subplots()
    x_pos = range(len(group_labels))
    ax.errorbar(
        x_pos,
        means,
        yerr=cis,
        fmt="o",
        capsize=5,
        label="Mean ± 95% CI",
    )
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(group_labels)
    ax.set_xlabel("Group")
    ax.set_ylabel("Response")
    ax.set_title("Mean ± 95% CI by Group")
    ax.legend()
    errorbar_path = os.path.join(args.output_dir, "errorbar.png")
    fig.savefig(errorbar_path)
    plt.close(fig)

    sys.exit(0)


if __name__ == "__main__":
    main()
