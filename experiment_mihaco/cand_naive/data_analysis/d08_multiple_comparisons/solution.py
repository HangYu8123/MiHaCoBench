"""
Data Analysis 08 — multiple_comparisons
K-Group Comparison with Family-Wise Error Control (Holm-Bonferroni)
"""

import argparse
import json
import os
import sys
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze a K-group experiment dataset with ANOVA and Holm-Bonferroni correction.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'group' (str) and 'value' (float).

    Returns
    -------
    dict with keys: group_means, n_per_group, anova_f, anova_p,
                    omnibus_significant, pairs, n_significant_pairs
    """
    # Compute per-group stats
    groups = sorted(df["group"].unique())
    group_data = {g: df[df["group"] == g]["value"].values for g in groups}

    group_means = {g: float(np.mean(group_data[g])) for g in groups}
    n_per_group = {g: int(len(group_data[g])) for g in groups}

    # Omnibus one-way ANOVA
    anova_result = f_oneway(*[group_data[g] for g in groups])
    anova_f = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    omnibus_significant = bool(anova_p < 0.05)

    # Pairwise t-tests (sorted label order)
    pair_keys = []
    raw_p_values = []
    t_stats = []

    for g1, g2 in combinations(groups, 2):
        # groups is already sorted, so g1 < g2 lexicographically
        key = f"{g1}_vs_{g2}"
        pair_keys.append(key)
        t_result = ttest_ind(group_data[g1], group_data[g2], equal_var=True)
        raw_p_values.append(float(t_result.pvalue))
        t_stats.append(float(t_result.statistic))

    # Holm-Bonferroni step-down correction
    m = len(raw_p_values)
    # Sort by raw p-value ascending, keep track of original indices
    sorted_indices = np.argsort(raw_p_values)
    adj_p_values = [0.0] * m

    prev_adj = 0.0
    for k, idx in enumerate(sorted_indices):
        raw_p = raw_p_values[idx]
        adj = raw_p * (m - k)
        adj = max(adj, prev_adj)  # enforce monotonicity
        adj = min(adj, 1.0)       # cap at 1.0
        adj_p_values[idx] = adj
        prev_adj = adj

    # Build pairs dict
    pairs = {}
    for i, key in enumerate(pair_keys):
        adj_p = adj_p_values[i]
        pairs[key] = {
            "raw_p": raw_p_values[i],
            "adj_p": adj_p,
            "significant": bool(adj_p < 0.05),
        }

    n_significant_pairs = sum(1 for v in pairs.values() if v["significant"])

    return {
        "group_means": group_means,
        "n_per_group": n_per_group,
        "anova_f": anova_f,
        "anova_p": anova_p,
        "omnibus_significant": omnibus_significant,
        "pairs": pairs,
        "n_significant_pairs": n_significant_pairs,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Multiple comparisons analysis")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        groups = sorted(results["group_means"].keys())

        # --- Plot 1: Bar chart of group means with error bars ---
        fig1, ax1 = plt.subplots(figsize=(8, 5))

        means = [results["group_means"][g] for g in groups]

        # Compute SEM for error bars
        group_data = {
            g: df[df["group"] == g]["value"].values for g in groups
        }
        sems = [
            float(np.std(group_data[g], ddof=1) / np.sqrt(len(group_data[g])))
            for g in groups
        ]

        ax1.bar(groups, means, yerr=sems, capsize=5, color="steelblue", alpha=0.8)
        ax1.set_xlabel("Group")
        ax1.set_ylabel("Mean Value")
        ax1.set_title("Group Means with SEM Error Bars")
        fig1.tight_layout()
        bar_chart_path = os.path.join(args.output_dir, "group_means_bar.png")
        fig1.savefig(bar_chart_path)
        plt.close(fig1)

        # --- Plot 2: Pairwise adjusted-p heatmap ---
        n_groups = len(groups)
        matrix = np.ones((n_groups, n_groups))

        group_idx = {g: i for i, g in enumerate(groups)}
        for pair_key, pair_vals in results["pairs"].items():
            g1, g2 = pair_key.split("_vs_")
            i, j = group_idx[g1], group_idx[g2]
            matrix[i, j] = pair_vals["adj_p"]
            matrix[j, i] = pair_vals["adj_p"]

        fig2, ax2 = plt.subplots(figsize=(6, 5))
        im = ax2.imshow(matrix, vmin=0.0, vmax=1.0, cmap="RdYlGn_r")
        fig2.colorbar(im, ax=ax2, label="Holm-adjusted p-value")
        ax2.set_xticks(range(n_groups))
        ax2.set_yticks(range(n_groups))
        ax2.set_xticklabels(groups)
        ax2.set_yticklabels(groups)
        ax2.set_title("Pairwise Holm-Bonferroni Adjusted p-values")

        # Annotate cells
        for i in range(n_groups):
            for j in range(n_groups):
                val = matrix[i, j]
                text = f"{val:.3f}" if i != j else "—"
                ax2.text(j, i, text, ha="center", va="center", fontsize=9)

        fig2.tight_layout()
        heatmap_path = os.path.join(args.output_dir, "pairwise_adj_p_heatmap.png")
        fig2.savefig(heatmap_path)
        plt.close(fig2)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
