"""Gold reference for data_analysis/d05_experiment_anova.

One-way ANOVA + Bonferroni-corrected pairwise t-tests on a three-group experiment.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless; must be set before pyplot import
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


_GROUPS = ["ctrl", "low", "high"]
_N_COMPARISONS = 3  # number of pairwise comparisons (3 choose 2)
_ALPHA = 0.05


def analyze(df: pd.DataFrame) -> dict:
    """Perform one-way ANOVA and Bonferroni-corrected pairwise t-tests.

    Parameters
    ----------
    df:
        DataFrame with columns ``group`` (str) and ``response`` (float).

    Returns
    -------
    dict with keys:
        group_means      – {group: mean_response}
        anova_F          – F-statistic from scipy.stats.f_oneway
        anova_p          – p-value from ANOVA
        significant      – True iff anova_p < 0.05
        significant_pairs – list of [g1, g2] pairs significant after Bonferroni
    """
    groups = sorted(df["group"].unique())

    # Group means
    group_means = {g: float(df.loc[df["group"] == g, "response"].mean()) for g in groups}

    # One-way ANOVA
    arrays = [df.loc[df["group"] == g, "response"].values for g in groups]
    anova_F, anova_p = stats.f_oneway(*arrays)
    anova_F = float(anova_F)
    anova_p = float(anova_p)
    significant = bool(anova_p < _ALPHA)

    # Pairwise t-tests with Bonferroni correction
    all_pairs = []
    for i, g1 in enumerate(groups):
        for j, g2 in enumerate(groups):
            if i < j:
                all_pairs.append((g1, g2))

    significant_pairs: list[list[str]] = []
    for g1, g2 in all_pairs:
        v1 = df.loc[df["group"] == g1, "response"].values
        v2 = df.loc[df["group"] == g2, "response"].values
        _, p_raw = stats.ttest_ind(v1, v2)
        p_corrected = min(float(p_raw) * _N_COMPARISONS, 1.0)
        if p_corrected < _ALPHA:
            pair = sorted([g1, g2])
            significant_pairs.append(pair)

    significant_pairs.sort()

    return {
        "group_means": group_means,
        "anova_F": anova_F,
        "anova_p": anova_p,
        "significant": significant,
        "significant_pairs": significant_pairs,
    }


def _make_boxplot(df: pd.DataFrame, output_path: Path) -> None:
    """Save a box plot of response per group."""
    groups = sorted(df["group"].unique())
    data_by_group = [df.loc[df["group"] == g, "response"].values for g in groups]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot(data_by_group, labels=groups)
    ax.set_xlabel("Group")
    ax.set_ylabel("Response")
    ax.set_title("Response Distribution by Group")
    fig.tight_layout()
    fig.savefig(str(output_path), dpi=80)
    plt.close(fig)


def _make_errorbar(df: pd.DataFrame, output_path: Path) -> None:
    """Save a mean ± 95 % CI error-bar chart."""
    groups = sorted(df["group"].unique())
    means = []
    cis = []
    for g in groups:
        vals = df.loc[df["group"] == g, "response"].values
        n = len(vals)
        mean = float(vals.mean())
        ci_half = 1.96 * float(vals.std(ddof=1)) / math.sqrt(n)
        means.append(mean)
        cis.append(ci_half)

    x_pos = list(range(len(groups)))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(x_pos, means, yerr=cis, fmt="o", capsize=5, linewidth=2)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(groups)
    ax.set_xlabel("Group")
    ax.set_ylabel("Mean Response")
    ax.set_title("Mean ± 95% CI by Group")
    fig.tight_layout()
    fig.savefig(str(output_path), dpi=80)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """CLI: --data <csv> --output-dir <dir>  writes results.json + 2 PNGs."""
    parser = argparse.ArgumentParser(description="One-way ANOVA experiment analysis.")
    parser.add_argument("--data", required=True, help="Path to experiment.csv")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write results.json
    with open(out_dir / "results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh)

    # Write plots
    _make_boxplot(df, out_dir / "boxplot.png")
    _make_errorbar(df, out_dir / "errorbar.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
