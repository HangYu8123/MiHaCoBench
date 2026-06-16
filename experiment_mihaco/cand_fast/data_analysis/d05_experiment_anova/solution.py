import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform one-way ANOVA and pairwise t-tests with Bonferroni correction.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'group' (str) and 'response' (float).

    Returns
    -------
    dict with keys:
        group_means, anova_F, anova_p, significant, significant_pairs
    """
    # Group means — cast to float to avoid numpy.float64 serialization issues
    group_means = {
        k: float(v)
        for k, v in df.groupby("group")["response"].mean().items()
    }

    # Extract per-group arrays
    arr_ctrl = df.loc[df["group"] == "ctrl", "response"].to_numpy()
    arr_low = df.loc[df["group"] == "low", "response"].to_numpy()
    arr_high = df.loc[df["group"] == "high", "response"].to_numpy()

    # One-way ANOVA
    anova_result = stats.f_oneway(arr_ctrl, arr_low, arr_high)
    anova_F = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    significant = bool(anova_p < 0.05)

    # Pairwise t-tests with Bonferroni correction (3 comparisons)
    # Pairs already alphabetically sorted
    pairs = [
        ("ctrl", "low"),
        ("ctrl", "high"),
        ("low", "high"),
    ]
    group_arrays = {
        "ctrl": arr_ctrl,
        "low": arr_low,
        "high": arr_high,
    }
    n_comparisons = 3

    significant_pairs = []
    for a, b in pairs:
        raw_p = stats.ttest_ind(group_arrays[a], group_arrays[b]).pvalue
        corrected_p = min(float(raw_p) * n_comparisons, 1.0)
        if corrected_p < 0.05:
            # Ensure alphabetical order in the pair
            pair = sorted([a, b])
            significant_pairs.append(pair)

    # Sort lexicographically (pairs are already in lex order from iteration,
    # but sort explicitly to be safe)
    significant_pairs.sort()

    return {
        "group_means": group_means,
        "anova_F": anova_F,
        "anova_p": anova_p,
        "significant": significant,
        "significant_pairs": significant_pairs,
    }


def main(argv: list = None):
    parser = argparse.ArgumentParser(
        description="One-Way ANOVA with Bonferroni Correction"
    )
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument(
        "--output-dir", required=True, help="Directory for output files"
    )
    args = parser.parse_args(argv)

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Load data
    df = pd.read_csv(args.data)

    # Run analysis
    result = analyze(df)

    # Write results.json
    results_path = os.path.join(args.output_dir, "results.json")
    with open(results_path, "w") as f:
        json.dump(result, f)

    # Extract group arrays for plotting (alphabetical order for consistency)
    arr_ctrl = df.loc[df["group"] == "ctrl", "response"].to_numpy()
    arr_low = df.loc[df["group"] == "low", "response"].to_numpy()
    arr_high = df.loc[df["group"] == "high", "response"].to_numpy()

    group_labels = ["ctrl", "low", "high"]
    group_data = [arr_ctrl, arr_low, arr_high]

    # Box plot
    fig, ax = plt.subplots()
    ax.boxplot(group_data, labels=group_labels)
    ax.set_title("Box Plot by Group")
    ax.set_xlabel("Group")
    ax.set_ylabel("Response")
    boxplot_path = os.path.join(args.output_dir, "boxplot.png")
    plt.savefig(boxplot_path)
    plt.close(fig)

    # Error-bar plot (mean +/- 95% CI using sample std ddof=1)
    means = []
    ci_half_widths = []
    for arr in group_data:
        m = float(np.mean(arr))
        s = float(np.std(arr, ddof=1))
        n = len(arr)
        ci_hw = 1.96 * s / np.sqrt(n)
        means.append(m)
        ci_half_widths.append(ci_hw)

    fig, ax = plt.subplots()
    x_pos = np.arange(len(group_labels))
    ax.errorbar(
        x_pos,
        means,
        yerr=ci_half_widths,
        fmt="o",
        capsize=5,
        linestyle="none",
    )
    ax.set_xticks(x_pos)
    ax.set_xticklabels(group_labels)
    ax.set_title("Mean +/- 95% CI by Group")
    ax.set_xlabel("Group")
    ax.set_ylabel("Response")
    errorbar_path = os.path.join(args.output_dir, "errorbar.png")
    plt.savefig(errorbar_path)
    plt.close(fig)

    sys.exit(0)


if __name__ == "__main__":
    main()
