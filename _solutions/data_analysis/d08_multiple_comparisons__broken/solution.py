"""Deliberately-broken reference for data_analysis/d08_multiple_comparisons.

Planted defect:
  Skips the Holm-Bonferroni multiple-comparisons correction entirely. The
  adjusted p-value is set equal to the RAW pairwise p-value and significance is
  declared from the raw p-value. This is the naive over-rejecting approach: a
  pair that is only marginally significant under raw t-tests (and should be
  demoted once family-wise error is controlled) is wrongly kept significant, so
  ``n_significant_pairs`` is too high.

The omnibus ANOVA, group means, sample sizes, and raw p-values are all still
correct, and the module imports and runs cleanly — only the correction step is
wrong, so the grader fails on the discriminator pair's adj_p / significant flag
and on n_significant_pairs.
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame, alpha: float = 0.05) -> dict:
    """Run an omnibus ANOVA plus pairwise t-tests — BROKEN: no Holm correction."""
    labels = sorted(df["group"].unique())
    groups = {lab: df.loc[df["group"] == lab, "value"].to_numpy(dtype=float)
              for lab in labels}

    group_means = {lab: float(np.mean(groups[lab])) for lab in labels}
    n_per_group = {lab: int(len(groups[lab])) for lab in labels}

    anova_f, anova_p = scipy.stats.f_oneway(*[groups[lab] for lab in labels])
    anova_f = float(anova_f)
    anova_p = float(anova_p)
    omnibus_significant = bool(anova_p < alpha)

    pairs: dict[str, dict] = {}
    n_significant_pairs = 0
    for x, y in combinations(labels, 2):
        key = f"{x}_vs_{y}"
        _, raw_p = scipy.stats.ttest_ind(groups[x], groups[y], equal_var=True)
        raw_p = float(raw_p)
        # BUG: no multiple-comparisons correction — adj_p is just the raw p,
        # and significance is declared straight from the raw p-value.
        adj_p = raw_p
        significant = bool(raw_p < alpha)
        if significant:
            n_significant_pairs += 1
        pairs[key] = {
            "raw_p": raw_p,
            "adj_p": adj_p,
            "significant": significant,
        }

    return {
        "group_means": group_means,
        "n_per_group": n_per_group,
        "anova_f": anova_f,
        "anova_p": anova_p,
        "omnibus_significant": omnibus_significant,
        "pairs": pairs,
        "n_significant_pairs": int(n_significant_pairs),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python solution.py --data <csv> --output-dir <dir>."""
    parser = argparse.ArgumentParser(
        description="K-group comparison with Holm-Bonferroni correction")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    labels = sorted(results["group_means"].keys())

    means = [results["group_means"][lab] for lab in labels]
    sems = []
    for lab in labels:
        vals = df.loc[df["group"] == lab, "value"].to_numpy(dtype=float)
        sems.append(float(np.std(vals, ddof=1) / np.sqrt(len(vals))))
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(labels, means, yerr=sems, capsize=6, color="steelblue",
           edgecolor="black", alpha=0.85)
    ax.set_title("Group means with standard-error bars")
    ax.set_xlabel("group")
    ax.set_ylabel("mean value")
    ax.axhline(0.0, color="gray", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(str(out_dir / "group_means.png"), dpi=80)
    plt.close(fig)

    k = len(labels)
    matrix = np.full((k, k), np.nan)
    idx = {lab: i for i, lab in enumerate(labels)}
    for key, info in results["pairs"].items():
        x, y = key.split("_vs_")
        i, j = idx[x], idx[y]
        matrix[i, j] = info["adj_p"]
        matrix[j, i] = info["adj_p"]
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    im = ax2.imshow(matrix, cmap="viridis", vmin=0.0, vmax=1.0)
    ax2.set_xticks(range(k))
    ax2.set_yticks(range(k))
    ax2.set_xticklabels(labels)
    ax2.set_yticklabels(labels)
    ax2.set_title("Pairwise Holm-adjusted p-values")
    for i in range(k):
        for j in range(k):
            if not np.isnan(matrix[i, j]):
                ax2.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center",
                         color="white", fontsize=8)
    fig2.colorbar(im, ax=ax2, label="adjusted p")
    fig2.tight_layout()
    fig2.savefig(str(out_dir / "pairwise_adjp.png"), dpi=80)
    plt.close(fig2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
