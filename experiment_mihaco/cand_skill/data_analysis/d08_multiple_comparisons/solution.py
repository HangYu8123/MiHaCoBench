"""
Data Analysis 08 — multiple_comparisons
K-Group Comparison with Family-Wise Error Control (Holm-Bonferroni)
"""
import argparse
import itertools
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")  # Must be set before importing pyplot
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyse a K-group experiment dataset.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'group' (str) and 'value' (float).

    Returns
    -------
    dict
        Analysis results with exactly: group_means, n_per_group, anova_f,
        anova_p, omnibus_significant, pairs, n_significant_pairs.
    """
    # Step A — Compute group means and n_per_group
    grouped = df.groupby("group")
    group_means = {label: float(mean) for label, mean in grouped["value"].mean().items()}
    n_per_group = {label: int(n) for label, n in grouped.size().items()}

    # Step B — ANOVA: extract arrays, call f_oneway
    labels = sorted(grouped.groups.keys())
    arrays = [grouped.get_group(label)["value"].values for label in labels]
    anova_result = f_oneway(*arrays)
    anova_f = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    omnibus_significant = bool(anova_p < 0.05)

    # Step C — Pairwise t-tests (all C(4,2)=6 pairs)
    pairs_raw = {}
    for a, b in itertools.combinations(labels, 2):
        key = f"{a}_vs_{b}"  # a < b since labels is sorted
        arr_a = grouped.get_group(a)["value"].values
        arr_b = grouped.get_group(b)["value"].values
        t_result = ttest_ind(arr_a, arr_b, equal_var=True)
        pairs_raw[key] = float(t_result.pvalue)

    # Step D — Holm-Bonferroni correction (manual implementation)
    m = len(pairs_raw)  # 6 comparisons
    # Sort pairs by raw_p ascending (stable sort)
    sorted_pairs = sorted(pairs_raw.items(), key=lambda x: x[1])

    # Compute adjusted p-values: for 0-indexed rank k, multiplier = m - k
    adj_p_values = []
    for k, (key, raw_p) in enumerate(sorted_pairs):
        multiplier = m - k
        adj = raw_p * multiplier
        adj_p_values.append(adj)

    # Enforce monotonicity: adj_p[k] = max(adj_p[k], adj_p[k-1])
    for k in range(1, len(adj_p_values)):
        adj_p_values[k] = max(adj_p_values[k], adj_p_values[k - 1])

    # Cap at 1.0
    adj_p_values = [min(v, 1.0) for v in adj_p_values]

    # Map adjusted values back to original pair keys
    pairs_adj = {}
    for (key, raw_p), adj_p in zip(sorted_pairs, adj_p_values):
        pairs_adj[key] = adj_p

    # Step E — Assemble the result dict
    pairs = {}
    for key in pairs_raw:
        raw_p = pairs_raw[key]
        adj_p = pairs_adj[key]
        pairs[key] = {
            "raw_p": float(raw_p),
            "adj_p": float(adj_p),
            "significant": bool(adj_p < 0.05),
        }

    n_significant_pairs = int(sum(1 for v in pairs.values() if v["significant"]))

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
    """
    CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(
        description="K-Group Comparison with Holm-Bonferroni correction"
    )
    parser.add_argument("--data", required=True, help="Path to CSV data file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        result = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        json_path = os.path.join(args.output_dir, "results.json")
        with open(json_path, "w") as f:
            f.write(json.dumps(result, indent=2))

        # Figure 1: Bar chart of group means with error bars (std)
        labels = sorted(df.groupby("group").groups.keys())
        means = [result["group_means"][label] for label in labels]
        stds = [float(df.groupby("group").get_group(label)["value"].std()) for label in labels]

        fig1, ax1 = plt.subplots(figsize=(8, 5))
        ax1.bar(labels, means, yerr=stds, capsize=5, color="steelblue", edgecolor="black")
        ax1.set_xlabel("Group")
        ax1.set_ylabel("Mean Value")
        ax1.set_title("Group Means with Standard Deviation Error Bars")
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, "group_means.png"), dpi=100)
        plt.close(fig1)

        # Figure 2: Pairwise adjusted-p heatmap (4x4 symmetric matrix)
        n_labels = len(labels)
        matrix = np.full((n_labels, n_labels), np.nan)

        for i, a in enumerate(labels):
            for j, b in enumerate(labels):
                if i == j:
                    continue
                # Determine the canonical key (X < Y lexicographically)
                if a < b:
                    key = f"{a}_vs_{b}"
                else:
                    key = f"{b}_vs_{a}"
                matrix[i, j] = result["pairs"][key]["adj_p"]

        # Replace NaN diagonal with 0 for display
        display_matrix = np.where(np.isnan(matrix), 0.0, matrix)

        fig2, ax2 = plt.subplots(figsize=(6, 5))
        im = ax2.imshow(display_matrix, vmin=0, vmax=1, cmap="RdYlGn_r")
        plt.colorbar(im, ax=ax2, label="Holm-adjusted p-value")
        ax2.set_xticks(range(n_labels))
        ax2.set_yticks(range(n_labels))
        ax2.set_xticklabels(labels)
        ax2.set_yticklabels(labels)
        ax2.set_title("Pairwise Holm-adjusted p-values")
        # Annotate cells
        for i in range(n_labels):
            for j in range(n_labels):
                if i != j:
                    ax2.text(j, i, f"{display_matrix[i, j]:.3f}",
                             ha="center", va="center", fontsize=9,
                             color="black")
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, "adj_p_heatmap.png"), dpi=100)
        plt.close(fig2)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
