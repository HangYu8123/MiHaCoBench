"""
solution.py — survey_correlation: Categorical Dependence & Numeric Correlation
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


NUMERIC_COLS = ["age", "income", "usage_hours", "satisfaction"]


def analyze(df: pd.DataFrame) -> dict:
    """Perform chi-square test and Pearson correlation analysis on survey data."""

    # 1. Chi-square test of independence on region × plan contingency table
    contingency = pd.crosstab(df["region"], df["plan"])
    chi2_stat, chi2_p, dof, expected = chi2_contingency(contingency)

    # 2. Pearson correlation among the four numeric columns
    corr_matrix = df[NUMERIC_COLS].corr()  # default method='pearson'

    # Find pair with highest absolute Pearson r among all unique pairs
    best_pair = None
    best_abs_r = -1.0
    best_r = None

    cols = NUMERIC_COLS
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr_matrix.loc[cols[i], cols[j]]
            abs_r = abs(r)
            if abs_r > best_abs_r:
                best_abs_r = abs_r
                best_r = r
                best_pair = sorted([cols[i], cols[j]])
            elif abs_r == best_abs_r:
                # Tie-breaking: alphabetical order of first, then second column name
                candidate = sorted([cols[i], cols[j]])
                if candidate < best_pair:
                    best_r = r
                    best_pair = candidate

    return {
        "chi2": float(chi2_stat),
        "chi2_p": float(chi2_p),
        "dof": int(dof),
        "dependent": bool(chi2_p < 0.05),
        "corr_strongest_pair": best_pair,
        "corr_strongest_r": float(best_r),
    }


def main(argv=None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Survey correlation analysis")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = analyze(df)

        # Write results.json
        with open(output_dir / "results.json", "w") as f:
            json.dump(results, f)

        # --- Plot 1: Correlation heatmap ---
        corr_matrix = df[NUMERIC_COLS].corr()

        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(corr_matrix.values, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
        plt.colorbar(im, ax=ax, label="Pearson r")
        ax.set_xticks(range(len(NUMERIC_COLS)))
        ax.set_yticks(range(len(NUMERIC_COLS)))
        ax.set_xticklabels(NUMERIC_COLS, rotation=45, ha="right")
        ax.set_yticklabels(NUMERIC_COLS)
        ax.set_title("Pearson Correlation Matrix")

        # Annotate each cell
        for i in range(len(NUMERIC_COLS)):
            for j in range(len(NUMERIC_COLS)):
                val = corr_matrix.values[i, j]
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=9)

        plt.tight_layout()
        fig.savefig(output_dir / "correlation_heatmap.png")
        plt.close(fig)

        # --- Plot 2: Grouped bar chart of region × plan crosstab ---
        contingency = pd.crosstab(df["region"], df["plan"])

        fig, ax = plt.subplots(figsize=(8, 5))
        contingency.plot(kind="bar", ax=ax)
        ax.set_title("Region × Plan Counts")
        ax.set_xlabel("Region")
        ax.set_ylabel("Count")
        ax.legend(title="Plan")
        plt.tight_layout()
        fig.savefig(output_dir / "region_plan_barchart.png")
        plt.close(fig)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
