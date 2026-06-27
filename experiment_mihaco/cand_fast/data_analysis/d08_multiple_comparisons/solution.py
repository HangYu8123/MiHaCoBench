"""
solution.py — K-Group Comparison with Family-Wise Error Control (Holm-Bonferroni)
"""

import argparse
import itertools
import json
import os

import matplotlib
matplotlib.use("Agg")  # must be before pyplot import; guards against missing MPLBACKEND
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


class _NpEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy scalar types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform omnibus ANOVA + pairwise t-tests with Holm-Bonferroni correction.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns 'group' (str) and 'value' (float).

    Returns
    -------
    dict with keys: group_means, n_per_group, anova_f, anova_p,
                    omnibus_significant, pairs, n_significant_pairs
    """
    # --- Group summaries ---
    labels = sorted(df["group"].unique())
    grouped = {lbl: df.loc[df["group"] == lbl, "value"].values for lbl in labels}

    group_means = {lbl: float(grouped[lbl].mean()) for lbl in labels}
    n_per_group = {lbl: int(len(grouped[lbl])) for lbl in labels}

    # --- Omnibus one-way ANOVA ---
    arrays = [grouped[lbl] for lbl in labels]
    anova_result = stats.f_oneway(*arrays)
    anova_f = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    omnibus_significant = bool(anova_p < 0.05)

    # --- Pairwise independent t-tests (equal_var=True = Student's t) ---
    pair_keys = [f"{a}_vs_{b}" for a, b in itertools.combinations(labels, 2)]
    raw_p_map = {}
    for key in pair_keys:
        a_lbl, b_lbl = key.split("_vs_")
        t_result = stats.ttest_ind(grouped[a_lbl], grouped[b_lbl], equal_var=True)
        raw_p_map[key] = float(t_result.pvalue)

    # --- Holm-Bonferroni step-down correction ---
    m = len(pair_keys)  # 6
    order = sorted(pair_keys, key=lambda k: raw_p_map[k])
    adj_p_map = {}
    prev = 0.0
    for i, key in enumerate(order):
        p = raw_p_map[key] * (m - i)
        p = max(p, prev)       # enforce monotonicity
        p = min(p, 1.0)        # cap at 1.0
        adj_p_map[key] = p
        prev = p

    # --- Build pairs dict ---
    pairs = {}
    for key in pair_keys:
        raw_p = raw_p_map[key]
        adj_p = adj_p_map[key]
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


def main(argv=None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="K-group comparison with Holm-Bonferroni correction."
    )
    parser.add_argument("--data", required=True, help="Path to input CSV file.")
    parser.add_argument("--output-dir", required=True, help="Directory for output files.")
    args = parser.parse_args(argv)

    # Read data
    df = pd.read_csv(args.data)

    # Run analysis
    result = analyze(df)

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # --- Write results.json ---
    json_path = os.path.join(args.output_dir, "results.json")
    with open(json_path, "w") as f:
        json.dump(result, f, cls=_NpEncoder, indent=2)

    # --- Plot 1: Bar chart of group means with SEM error bars ---
    labels = sorted(df["group"].unique())
    means = pd.Series(result["group_means"])
    sem = df.groupby("group")["value"].sem()

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(labels, means.loc[labels], yerr=sem.loc[labels], capsize=5,
           color="steelblue", alpha=0.8, edgecolor="black")
    ax.set_xlabel("Group")
    ax.set_ylabel("Mean value")
    ax.set_title("Group Means with SEM Error Bars")
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "group_means.png"), dpi=100)
    plt.close()

    # --- Plot 2: Heatmap of Holm-adjusted p-values ---
    n = len(labels)
    label_idx = {lbl: i for i, lbl in enumerate(labels)}
    matrix = np.ones((n, n))  # diagonal = 1.0; off-diagonal filled below

    for key, vals in result["pairs"].items():
        a_lbl, b_lbl = key.split("_vs_")
        i, j = label_idx[a_lbl], label_idx[b_lbl]
        matrix[i, j] = vals["adj_p"]
        matrix[j, i] = vals["adj_p"]  # symmetric

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix, vmin=0, vmax=1, cmap="viridis_r")
    plt.colorbar(im, ax=ax, label="Holm-adjusted p-value")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_title("Pairwise Holm-Adjusted p-values")

    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{matrix[i, j]:.3f}",
                    ha="center", va="center", fontsize=9,
                    color="white" if matrix[i, j] < 0.5 else "black")

    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "adj_p_heatmap.png"), dpi=100)
    plt.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
