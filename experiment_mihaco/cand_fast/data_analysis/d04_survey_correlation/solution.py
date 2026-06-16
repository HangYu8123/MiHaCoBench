import matplotlib
matplotlib.use("Agg")

import argparse
import itertools
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform chi-square test of independence (region x plan) and
    Pearson correlation among numeric columns.

    Returns a dict with keys:
        chi2, chi2_p, dof, dependent, corr_strongest_pair, corr_strongest_r
    """
    # --- Chi-square test ---
    contingency_table = pd.crosstab(df["region"], df["plan"])
    chi2_stat, chi2_p, dof, expected = chi2_contingency(contingency_table)

    chi2_stat = float(chi2_stat)
    chi2_p = float(chi2_p)
    dof = int(dof)
    dependent = bool(chi2_p < 0.05)

    # --- Pearson correlation ---
    numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
    corr_matrix = df[numeric_cols].corr()

    # Iterate unique pairs; pre-sort column names for deterministic tie-breaking
    sorted_cols = sorted(numeric_cols)  # alphabetical: ["age", "income", "satisfaction", "usage_hours"]

    best_pair = None
    best_abs_r = -1.0
    best_r = None

    for col_a, col_b in itertools.combinations(sorted_cols, 2):
        r_val = corr_matrix.loc[col_a, col_b]
        abs_r = abs(r_val)
        if abs_r > best_abs_r:
            best_abs_r = abs_r
            best_pair = (col_a, col_b)
            best_r = float(r_val)

    # corr_strongest_pair sorted alphabetically (already guaranteed by combinations on sorted list)
    corr_strongest_pair = sorted([best_pair[0], best_pair[1]])
    corr_strongest_r = best_r

    return {
        "chi2": chi2_stat,
        "chi2_p": chi2_p,
        "dof": dof,
        "dependent": dependent,
        "corr_strongest_pair": corr_strongest_pair,
        "corr_strongest_r": corr_strongest_r,
    }


def main(argv=None) -> int:
    """
    CLI entry point:
        python solution.py --data <csv_path> --output-dir <dir>

    Writes:
        results.json
        corr_heatmap.png
        region_plan_bar.png
    """
    parser = argparse.ArgumentParser(description="Survey correlation analysis")
    parser.add_argument("--data", required=True, help="Path to survey CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory for results")
    args = parser.parse_args(argv)

    try:
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        df = pd.read_csv(args.data)
        result = analyze(df)

        # Write results.json
        results_path = os.path.join(output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result, f, indent=2)

        # --- Heatmap of correlation matrix ---
        numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
        corr_matrix = df[numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(corr_matrix.values, vmin=-1, vmax=1, cmap="coolwarm")
        plt.colorbar(im, ax=ax)
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
        ax.set_yticklabels(numeric_cols)
        ax.set_title("Pearson Correlation Heatmap")

        # Annotate cells with correlation values
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                val = corr_matrix.values[i, j]
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8,
                        color="black")

        plt.tight_layout()
        heatmap_path = os.path.join(output_dir, "corr_heatmap.png")
        plt.savefig(heatmap_path)
        plt.close()

        # --- Grouped bar chart of region x plan ---
        contingency_table = pd.crosstab(df["region"], df["plan"])

        fig, ax = plt.subplots(figsize=(7, 5))
        contingency_table.plot(kind="bar", ax=ax)
        ax.set_title("Region × Plan Counts")
        ax.set_xlabel("Region")
        ax.set_ylabel("Count")
        ax.legend(title="Plan")
        plt.xticks(rotation=0)
        plt.tight_layout()
        bar_path = os.path.join(output_dir, "region_plan_bar.png")
        plt.savefig(bar_path)
        plt.close()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
