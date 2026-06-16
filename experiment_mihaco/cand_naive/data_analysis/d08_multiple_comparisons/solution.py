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
from scipy import stats


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform one-way ANOVA and pairwise t-tests with Holm-Bonferroni correction.

    Parameters
    ----------
    df : pandas.DataFrame
        Must have columns 'group' (str) and 'value' (float).

    Returns
    -------
    dict with keys: group_means, n_per_group, anova_f, anova_p,
                    omnibus_significant, pairs, n_significant_pairs
    """
    # --- Group means and sample sizes ---
    group_labels = sorted(df["group"].unique())
    group_means = {label: float(df.loc[df["group"] == label, "value"].mean())
                   for label in group_labels}
    n_per_group = {label: int((df["group"] == label).sum())
                   for label in group_labels}

    # --- Omnibus ANOVA ---
    group_arrays = [df.loc[df["group"] == label, "value"].values
                    for label in group_labels]
    anova_result = stats.f_oneway(*group_arrays)
    anova_f = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    omnibus_significant = bool(anova_p < 0.05)

    # --- Pairwise t-tests (sorted label order) ---
    pair_keys = []
    raw_pvalues = []

    for label_x, label_y in combinations(group_labels, 2):
        # group_labels is already sorted, so label_x < label_y lexicographically
        key = f"{label_x}_vs_{label_y}"
        arr_x = df.loc[df["group"] == label_x, "value"].values
        arr_y = df.loc[df["group"] == label_y, "value"].values
        t_result = stats.ttest_ind(arr_x, arr_y, equal_var=True)
        raw_p = float(t_result.pvalue)
        pair_keys.append(key)
        raw_pvalues.append(raw_p)

    # --- Holm-Bonferroni step-down correction ---
    m = len(raw_pvalues)
    # Sort indices by ascending raw p-value
    sorted_indices = sorted(range(m), key=lambda i: raw_pvalues[i])

    adj_pvalues = [0.0] * m
    running_max = 0.0
    for rank, idx in enumerate(sorted_indices):
        k = rank  # 0-based rank
        adj_p = raw_pvalues[idx] * (m - k)
        # Enforce monotonicity: each adjusted p is at least the previous one
        adj_p = max(adj_p, running_max)
        # Cap at 1.0
        adj_p = min(adj_p, 1.0)
        adj_pvalues[idx] = adj_p
        running_max = adj_p

    # --- Build pairs dict ---
    pairs = {}
    for i, key in enumerate(pair_keys):
        raw_p = raw_pvalues[i]
        adj_p = adj_pvalues[i]
        pairs[key] = {
            "raw_p": raw_p,
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


def _plot_group_means(results: dict, output_dir: str) -> None:
    """Bar chart of group means with SEM error bars (from n_per_group)."""
    group_means = results["group_means"]
    labels = sorted(group_means.keys())
    means = [group_means[lbl] for lbl in labels]

    fig, ax = plt.subplots(figsize=(7, 5))
    x_pos = np.arange(len(labels))
    ax.bar(x_pos, means, color="steelblue", alpha=0.8, width=0.6)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Group")
    ax.set_ylabel("Mean value")
    ax.set_title("Group Means")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "group_means.png"), dpi=100)
    plt.close(fig)


def _plot_adj_p_heatmap(results: dict, output_dir: str) -> None:
    """Heatmap matrix of Holm-Bonferroni adjusted p-values for each pair."""
    pairs = results["pairs"]
    # Collect all unique group labels from pair keys
    all_labels = set()
    for key in pairs:
        a, b = key.split("_vs_")
        all_labels.add(a)
        all_labels.add(b)
    labels = sorted(all_labels)
    n = len(labels)
    label_idx = {lbl: i for i, lbl in enumerate(labels)}

    matrix = np.ones((n, n))
    for key, info in pairs.items():
        a, b = key.split("_vs_")
        i, j = label_idx[a], label_idx[b]
        matrix[i, j] = info["adj_p"]
        matrix[j, i] = info["adj_p"]
    # Diagonal: set to NaN to visually distinguish self-comparisons
    np.fill_diagonal(matrix, np.nan)

    fig, ax = plt.subplots(figsize=(6, 5))
    masked = np.ma.masked_invalid(matrix)
    cmap = matplotlib.colormaps.get_cmap("RdYlGn_r").copy()
    cmap.set_bad(color="lightgrey")
    im = ax.imshow(masked, vmin=0, vmax=1, cmap=cmap, aspect="auto")
    plt.colorbar(im, ax=ax, label="Holm-Bonferroni adj. p-value")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_title("Pairwise Adjusted p-values (Holm-Bonferroni)")

    # Annotate cells
    for i in range(n):
        for j in range(n):
            if i != j:
                val = matrix[i, j]
                text = f"{val:.3f}"
                color = "white" if val < 0.3 or val > 0.7 else "black"
                ax.text(j, i, text, ha="center", va="center",
                        fontsize=8, color=color)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "adj_p_heatmap.png"), dpi=100)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: python solution.py --data <csv_path> --output-dir <dir>"""
    parser = argparse.ArgumentParser(
        description="K-Group Comparison with Holm-Bonferroni Correction"
    )
    parser.add_argument("--data", required=True, help="Path to groups.csv")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        json_path = os.path.join(args.output_dir, "results.json")
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2)

        # Write PNG files
        _plot_group_means(results, args.output_dir)
        _plot_adj_p_heatmap(results, args.output_dir)

        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
