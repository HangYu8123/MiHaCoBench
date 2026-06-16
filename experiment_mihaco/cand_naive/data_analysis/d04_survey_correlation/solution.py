"""
Data Analysis 04 — survey_correlation
Categorical Dependence & Numeric Correlation
"""
import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


NUMERIC_COLS = ["age", "income", "usage_hours", "satisfaction"]


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform chi-square test (region x plan) and Pearson correlation
    analysis on the four numeric columns.

    Returns a dict with keys:
        chi2, chi2_p, dof, dependent, corr_strongest_pair, corr_strongest_r
    """
    # 1. Chi-square test of independence on region x plan contingency table
    contingency = pd.crosstab(df["region"], df["plan"])
    chi2_stat, p_value, dof, _ = chi2_contingency(contingency)

    dependent = bool(p_value < 0.05)

    # 2. Pearson correlation among the four numeric columns
    corr_matrix = df[NUMERIC_COLS].corr()

    # Find the pair with the highest absolute Pearson r among unique pairs
    best_abs_r = -1.0
    best_pair = None
    best_r = None

    cols = NUMERIC_COLS
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            col_a = cols[i]
            col_b = cols[j]
            r = corr_matrix.loc[col_a, col_b]
            abs_r = abs(r)
            if abs_r > best_abs_r:
                best_abs_r = abs_r
                best_pair = sorted([col_a, col_b])
                best_r = r
            elif abs_r == best_abs_r:
                # Tie-break: alphabetically by first col, then second col
                candidate_pair = sorted([col_a, col_b])
                if candidate_pair < best_pair:
                    best_pair = candidate_pair
                    best_r = r

    # Get r value for the best pair (use sorted order lookup)
    # best_r is the r value found when we detected the best pair
    # but since pair is sorted, we need to look it up from the sorted pair
    final_r = float(corr_matrix.loc[best_pair[0], best_pair[1]])

    return {
        "chi2": float(chi2_stat),
        "chi2_p": float(p_value),
        "dof": int(dof),
        "dependent": dependent,
        "corr_strongest_pair": best_pair,
        "corr_strongest_r": final_r,
    }


def _plot_correlation_heatmap(df: pd.DataFrame, output_dir: str) -> None:
    """Save a heatmap of the 4x4 Pearson correlation matrix."""
    corr_matrix = df[NUMERIC_COLS].corr()

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr_matrix.values, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
    plt.colorbar(im, ax=ax, label="Pearson r")

    ax.set_xticks(range(len(NUMERIC_COLS)))
    ax.set_yticks(range(len(NUMERIC_COLS)))
    ax.set_xticklabels(NUMERIC_COLS, rotation=45, ha="right")
    ax.set_yticklabels(NUMERIC_COLS)

    # Annotate cells with r values
    for i in range(len(NUMERIC_COLS)):
        for j in range(len(NUMERIC_COLS)):
            val = corr_matrix.values[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=9,
                    color="black")

    ax.set_title("Pearson Correlation Matrix")
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "correlation_heatmap.png"), dpi=100)
    plt.close(fig)


def _plot_region_plan_bar(df: pd.DataFrame, output_dir: str) -> None:
    """Save a grouped bar chart of the region x plan contingency table."""
    contingency = pd.crosstab(df["region"], df["plan"])

    fig, ax = plt.subplots(figsize=(8, 5))
    contingency.plot(kind="bar", ax=ax)
    ax.set_title("Region × Plan Distribution")
    ax.set_xlabel("Region")
    ax.set_ylabel("Count")
    ax.legend(title="Plan")
    plt.xticks(rotation=0)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "region_plan_bar.png"), dpi=100)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Survey correlation analysis")
    parser.add_argument("--data", required=True, help="Path to survey CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return 1

    try:
        results = analyze(df)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        return 1

    try:
        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        # Save PNG visualizations
        _plot_correlation_heatmap(df, args.output_dir)
        _plot_region_plan_bar(df, args.output_dir)

    except Exception as e:
        print(f"Error writing outputs: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
