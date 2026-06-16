"""
Data Analysis 05 — experiment_anova
One-Way ANOVA with Bonferroni correction.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Must be called before importing pyplot
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def analyze(df: pd.DataFrame) -> dict:
    """Perform one-way ANOVA and pairwise t-tests with Bonferroni correction.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'group' (str) and 'response' (float).

    Returns
    -------
    dict with keys:
        group_means, anova_F, anova_p, significant, significant_pairs
    """
    group_names = ["ctrl", "low", "high"]
    group_data = {g: df[df["group"] == g]["response"].values for g in group_names}

    # Group means — cast to Python float for JSON serialization
    group_means = {g: float(np.mean(group_data[g])) for g in group_names}

    # One-way ANOVA
    f_stat, p_val = stats.f_oneway(*[group_data[g] for g in group_names])
    anova_F = float(f_stat)
    anova_p = float(p_val)
    significant = bool(anova_p < 0.05)

    # Pairwise Bonferroni-corrected t-tests
    # Pairs in alphabetical order; each pair is sorted alphabetically
    pairs = [("ctrl", "high"), ("ctrl", "low"), ("low", "high")]
    significant_pairs = []
    for a, b in pairs:
        result = stats.ttest_ind(group_data[a], group_data[b])
        corrected_p = min(float(result.pvalue) * 3, 1.0)
        if corrected_p < 0.05:
            significant_pairs.append(sorted([a, b]))

    # Sort for determinism (already in order but apply sorted() as spec requires)
    significant_pairs = sorted(significant_pairs)

    return {
        "group_means": group_means,
        "anova_F": anova_F,
        "anova_p": anova_p,
        "significant": significant,
        "significant_pairs": significant_pairs,
    }


def main(argv=None):
    """CLI entry point.

    Usage:
        python solution.py --data <path_to_csv> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(
        description="One-Way ANOVA with Bonferroni correction"
    )
    parser.add_argument("--data", required=True, help="Path to the input CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory to write outputs")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_csv(args.data)

    # Analyze
    result = analyze(df)

    # Write results.json
    with open(output_dir / "results.json", "w") as f:
        json.dump(result, f)

    # Prepare group data for plots
    group_names = ["ctrl", "low", "high"]
    group_data = {g: df[df["group"] == g]["response"].values for g in group_names}

    # Boxplot
    fig, ax = plt.subplots()
    ax.boxplot([group_data[g] for g in group_names])
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(group_names)
    ax.set_title("Response by Group")
    ax.set_ylabel("Response")
    fig.savefig(output_dir / "boxplot.png")
    plt.close(fig)

    # Errorbar (mean ± 95% CI)
    means = [float(np.mean(group_data[g])) for g in group_names]
    cis = [
        1.96 * float(np.std(group_data[g], ddof=1)) / np.sqrt(len(group_data[g]))
        for g in group_names
    ]
    fig, ax = plt.subplots()
    ax.errorbar(x=[0, 1, 2], y=means, yerr=cis, fmt="o", capsize=5)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(group_names)
    ax.set_title("Mean ± 95% CI by Group")
    ax.set_ylabel("Response")
    fig.savefig(output_dir / "errorbar.png")
    plt.close(fig)

    sys.exit(0)


if __name__ == "__main__":
    main()
