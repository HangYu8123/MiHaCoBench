"""
solution.py — One-Way ANOVA with Bonferroni Correction
"""

import argparse
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind


def analyze(df: pd.DataFrame) -> dict:
    """Perform one-way ANOVA and pairwise t-tests with Bonferroni correction."""
    groups = ['ctrl', 'low', 'high']

    # Per-group response arrays
    data = {g: df.loc[df['group'] == g, 'response'].values for g in groups}

    # Group means — explicit order: ctrl, low, high; convert to plain Python float
    group_means = {g: float(data[g].mean()) for g in groups}

    # One-way ANOVA
    f_stat, p_val = f_oneway(data['ctrl'], data['low'], data['high'])
    anova_F = float(f_stat)
    anova_p = float(p_val)
    significant = bool(anova_p < 0.05)

    # Bonferroni pairwise t-tests — fixed pair iteration order (already alpha-sorted within pair)
    pairs_to_test = [('ctrl', 'low'), ('ctrl', 'high'), ('low', 'high')]
    n_comparisons = 3
    significant_pairs = []
    for g1, g2 in pairs_to_test:
        _, raw_p = ttest_ind(data[g1], data[g2], equal_var=True)
        corrected_p = min(float(raw_p) * n_comparisons, 1.0)
        if corrected_p < 0.05:
            # Pair is already alphabetically sorted; add as list
            significant_pairs.append([g1, g2])

    # Sort output list lexicographically by first then second element
    significant_pairs.sort(key=lambda pair: (pair[0], pair[1]))

    return {
        'group_means': group_means,
        'anova_F': anova_F,
        'anova_p': anova_p,
        'significant': significant,
        'significant_pairs': significant_pairs,
    }


def main(argv=None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='One-Way ANOVA with Bonferroni Correction')
    parser.add_argument('--data', required=True, help='Path to input CSV file')
    parser.add_argument('--output-dir', dest='output_dir', required=True,
                        help='Directory for output files')
    args = parser.parse_args(argv)

    # Read data
    df = pd.read_csv(args.data)

    # Run analysis
    result = analyze(df)

    # Create output directory if needed
    os.makedirs(args.output_dir, exist_ok=True)

    # Write results.json
    with open(os.path.join(args.output_dir, 'results.json'), 'w') as f:
        json.dump(result, f)

    groups = ['ctrl', 'low', 'high']
    data_lists = [df.loc[df['group'] == g, 'response'].values for g in groups]

    # Boxplot: one box per group
    fig, ax = plt.subplots()
    ax.boxplot(data_lists, tick_labels=groups)
    ax.set_title('Response by Group')
    ax.set_xlabel('Group')
    ax.set_ylabel('Response')
    fig.savefig(os.path.join(args.output_dir, 'boxplot.png'))
    plt.close(fig)

    # Errorbar: mean ± 95% CI (1.96 * std / sqrt(n))
    means = []
    ci_halfwidths = []
    for g in groups:
        arr = df.loc[df['group'] == g, 'response'].values
        n = len(arr)
        std = float(np.std(arr, ddof=1))
        mean = float(np.mean(arr))
        means.append(mean)
        ci_halfwidths.append(1.96 * std / np.sqrt(n))

    x_positions = list(range(len(groups)))
    fig, ax = plt.subplots()
    ax.errorbar(x_positions, means, yerr=ci_halfwidths, fmt='o', capsize=5)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(groups)
    ax.set_title('Mean ± 95% CI by Group')
    ax.set_xlabel('Group')
    ax.set_ylabel('Mean Response')
    fig.savefig(os.path.join(args.output_dir, 'errorbar.png'))
    plt.close(fig)


if __name__ == '__main__':
    main()
