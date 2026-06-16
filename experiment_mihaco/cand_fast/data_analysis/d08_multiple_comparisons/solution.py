import matplotlib
matplotlib.use("Agg")

import argparse
import itertools
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Analyze a K-group dataset with omnibus ANOVA and Holm-Bonferroni correction."""

    # Group data
    labels = sorted(df["group"].unique().tolist())
    grouped = df.groupby("group")

    # Group means (native Python float)
    group_means = {label: float(grouped["value"].mean()[label]) for label in labels}

    # n_per_group (native Python int)
    n_per_group = {label: int(grouped["value"].count()[label]) for label in labels}

    # Omnibus ANOVA using scipy.stats.f_oneway
    group_arrays = [grouped.get_group(label)["value"].values for label in labels]
    anova_result = scipy.stats.f_oneway(*group_arrays)
    anova_f = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    omnibus_significant = bool(anova_p < 0.05)

    # Pairwise t-tests
    pair_keys = []
    raw_pvalues = []

    for X, Y in itertools.combinations(labels, 2):
        # labels is already sorted, so X < Y lexicographically
        key = f"{X}_vs_{Y}"
        a = grouped.get_group(X)["value"].values
        b = grouped.get_group(Y)["value"].values
        ttest_result = scipy.stats.ttest_ind(a, b, equal_var=True)
        raw_p = float(ttest_result.pvalue)
        pair_keys.append(key)
        raw_pvalues.append(raw_p)

    # Holm-Bonferroni step-down correction
    m = len(raw_pvalues)  # number of comparisons = 6
    # Sort ascending by raw p-value
    sorted_indices = sorted(range(m), key=lambda i: raw_pvalues[i])

    adj_pvalues = [0.0] * m
    prev_adj = 0.0
    for k, idx in enumerate(sorted_indices):
        raw_p = raw_pvalues[idx]
        adj_p = raw_p * (m - k)
        # Enforce monotonicity: adj_p >= previous adjusted p
        adj_p = max(adj_p, prev_adj)
        # Cap at 1.0
        adj_p = min(adj_p, 1.0)
        adj_pvalues[idx] = adj_p
        prev_adj = adj_p

    # Build pairs dict
    pairs = {}
    for i, key in enumerate(pair_keys):
        raw_p = raw_pvalues[i]
        adj_p = adj_pvalues[i]
        pairs[key] = {
            "raw_p": raw_p,
            "adj_p": adj_p,
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
    parser = argparse.ArgumentParser(description="Multiple comparisons analysis")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        result = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result, f, indent=2)

        # --- Bar chart of group means with error bars ---
        labels = sorted(result["group_means"].keys())
        means = [result["group_means"][label] for label in labels]

        # Compute standard errors for error bars
        grouped = df.groupby("group")["value"]
        stds = [float(grouped.std()[label]) for label in labels]
        ns = [result["n_per_group"][label] for label in labels]
        sems = [s / np.sqrt(n) for s, n in zip(stds, ns)]

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(labels, means, yerr=sems, capsize=5, color="steelblue", alpha=0.8)
        ax.set_xlabel("Group")
        ax.set_ylabel("Mean value")
        ax.set_title("Group Means with Standard Error")
        fig.tight_layout()
        bar_path = os.path.join(args.output_dir, "group_means_bar.png")
        fig.savefig(bar_path)
        plt.close(fig)

        # --- Heatmap of adjusted p-values ---
        n_labels = len(labels)
        # Build symmetric matrix; diagonal = NaN
        matrix = np.full((n_labels, n_labels), np.nan)
        label_idx = {label: i for i, label in enumerate(labels)}

        for pair_key, pair_info in result["pairs"].items():
            X, Y = pair_key.split("_vs_")
            i = label_idx[X]
            j = label_idx[Y]
            matrix[i, j] = pair_info["adj_p"]
            matrix[j, i] = pair_info["adj_p"]

        fig, ax = plt.subplots(figsize=(6, 5))
        # Use masked array to handle NaN on diagonal
        masked = np.ma.masked_invalid(matrix)
        cmap = plt.cm.RdYlGn_r
        im = ax.imshow(masked, vmin=0.0, vmax=1.0, cmap=cmap, aspect="auto")
        plt.colorbar(im, ax=ax, label="Holm-Bonferroni adjusted p-value")

        ax.set_xticks(range(n_labels))
        ax.set_yticks(range(n_labels))
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)
        ax.set_title("Pairwise Adjusted p-value Heatmap")

        # Annotate cells
        for i in range(n_labels):
            for j in range(n_labels):
                if not np.isnan(matrix[i, j]):
                    val = matrix[i, j]
                    text_color = "white" if val > 0.7 else "black"
                    ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                            fontsize=9, color=text_color)

        fig.tight_layout()
        heatmap_path = os.path.join(args.output_dir, "pairwise_adj_p_heatmap.png")
        fig.savefig(heatmap_path)
        plt.close(fig)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
