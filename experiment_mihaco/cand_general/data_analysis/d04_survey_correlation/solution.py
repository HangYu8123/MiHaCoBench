"""
Data Analysis 04 — survey_correlation
Categorical Dependence & Numeric Correlation
"""

import argparse
import itertools
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")  # Belt-and-suspenders; env also sets MPLBACKEND=Agg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Perform chi-square test and Pearson correlation analysis on survey data."""

    # --- 1. Chi-square test of independence: region × plan ---
    ct = pd.crosstab(df["region"], df["plan"])
    chi2, p, dof, expected = scipy.stats.chi2_contingency(ct)

    # Cast to Python-native types to ensure JSON serializability
    chi2 = float(chi2)
    p = float(p)
    dof = int(dof)
    dependent = bool(p < 0.05)

    # --- 2. Pearson correlation among numeric columns ---
    numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
    corr = df[numeric_cols].corr()

    # Iterate upper-triangle pairs in alphabetical order
    sorted_cols = sorted(numeric_cols)
    best_pair = None
    best_abs_r = -1.0

    for c1, c2 in itertools.combinations(sorted_cols, 2):
        r_val = float(corr.loc[c1, c2])
        abs_r = abs(r_val)
        if abs_r > best_abs_r:
            best_abs_r = abs_r
            best_pair = (c1, c2)
            best_r = r_val

    # Retrieve final signed r value
    corr_strongest_r = float(best_r)
    corr_strongest_pair = list(best_pair)  # Already alphabetically sorted

    return {
        "chi2": chi2,
        "chi2_p": p,
        "dof": dof,
        "dependent": dependent,
        "corr_strongest_pair": corr_strongest_pair,
        "corr_strongest_r": corr_strongest_r,
    }


def main(argv=None) -> int:
    """CLI entry point: reads CSV, runs analysis, writes outputs."""
    try:
        parser = argparse.ArgumentParser(
            description="Survey correlation analysis"
        )
        parser.add_argument("--data", required=True, help="Path to survey CSV file")
        parser.add_argument(
            "--output-dir", required=True, help="Directory for output files"
        )
        args = parser.parse_args(argv)

        data_path = args.data
        output_dir = args.output_dir

        # Read data
        df = pd.read_csv(data_path)

        # Run analysis
        result = analyze(df)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # --- Write results.json ---
        results_path = os.path.join(output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result, f)

        # --- Figure 1: Correlation heatmap ---
        numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
        corr = df[numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm")
        plt.colorbar(im, ax=ax)
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
        ax.set_yticklabels(numeric_cols)
        ax.set_title("Pearson Correlation Heatmap")

        # Annotate each cell with the r value
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                val = corr.values[i, j]
                ax.text(
                    j, i, f"{val:.2f}",
                    ha="center", va="center", fontsize=9,
                    color="black"
                )

        fig.tight_layout()
        heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
        fig.savefig(heatmap_path, dpi=100)
        plt.close("all")

        # --- Figure 2: Region × Plan grouped bar chart ---
        ct = pd.crosstab(df["region"], df["plan"])

        fig, ax = plt.subplots(figsize=(8, 5))
        ct.plot(kind="bar", ax=ax)
        ax.set_title("Region × Plan Counts")
        ax.set_xlabel("Region")
        ax.set_ylabel("Count")
        ax.legend(title="Plan")
        plt.xticks(rotation=0)
        fig.tight_layout()
        chart_path = os.path.join(output_dir, "region_plan_chart.png")
        fig.savefig(chart_path, dpi=100)
        plt.close("all")

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
