"""Deliberately-broken reference for data_analysis/d04_survey_correlation.

Planted defects:
  1. Wrong dof: uses n_rows * n_cols - 1 = 11 instead of (n_rows-1)*(n_cols-1) = 6.
     This makes the dof test fail definitively.
  2. corr_strongest_r is returned as abs(r) instead of the signed r.
     For the income/usage_hours pair, gold r ~ 0.81 (positive), so abs
     is the same sign — but this defect exposes incorrect implementation.
     The dof bug alone is sufficient for >=1 failure.

These defects make the grader fail >=1 test (specifically test_dof_correct).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Broken: wrong dof computation."""
    # Chi-square test
    ct = pd.crosstab(df["region"], df["plan"])
    chi2, chi2_p, dof, _expected = scipy.stats.chi2_contingency(ct)

    dependent = bool(chi2_p < 0.05)

    # BUG: dof is computed incorrectly — using flat count minus 1
    # instead of the correct (n_regions - 1) * (n_plans - 1)
    n_rows, n_cols = ct.shape
    wrong_dof = n_rows * n_cols - 1  # = 4*3 - 1 = 11; correct is (4-1)*(3-1) = 6

    # Pearson correlation (correct)
    numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
    corr_matrix = df[numeric_cols].corr()

    best_abs_r = -1.0
    best_pair: list[str] = []
    best_r = 0.0

    for i, c1 in enumerate(numeric_cols):
        for j, c2 in enumerate(numeric_cols):
            if i >= j:
                continue
            r = float(corr_matrix.loc[c1, c2])
            pair_sorted = sorted([c1, c2])
            abs_r = abs(r)
            if abs_r > best_abs_r or (
                abs_r == best_abs_r and pair_sorted < best_pair
            ):
                best_abs_r = abs_r
                best_pair = pair_sorted
                best_r = r

    return {
        "chi2": float(chi2),
        "chi2_p": float(chi2_p),
        "dof": wrong_dof,  # BUG: 11 instead of 6
        "dependent": dependent,
        "corr_strongest_pair": best_pair,
        "corr_strongest_r": best_r,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python solution.py --data <csv_path> --output-dir <dir>."""
    parser = argparse.ArgumentParser(description="Survey correlation analysis")
    parser.add_argument("--data", required=True, help="Path to the survey CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
    corr_matrix = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(7, 6))
    cax = ax.imshow(corr_matrix.values, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
    fig.colorbar(cax, ax=ax, label="Pearson r")
    ax.set_xticks(range(len(numeric_cols)))
    ax.set_yticks(range(len(numeric_cols)))
    ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
    ax.set_yticklabels(numeric_cols)
    ax.set_title("Numeric Correlation Heatmap")
    fig.tight_layout()
    fig.savefig(str(out_dir / "corr_heatmap.png"), dpi=80)
    plt.close(fig)

    ct = pd.crosstab(df["region"], df["plan"])
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ct.plot(kind="bar", ax=ax2, colormap="tab10", edgecolor="black")
    ax2.set_title("Region x Plan Crosstab")
    ax2.set_xlabel("Region")
    ax2.set_ylabel("Count")
    fig2.tight_layout()
    fig2.savefig(str(out_dir / "region_plan_bar.png"), dpi=80)
    plt.close(fig2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
