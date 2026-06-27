import matplotlib
matplotlib.use("Agg")

import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import chi2_contingency


def analyze(df: pd.DataFrame) -> dict:
    """Perform chi-square test and Pearson correlation analysis on survey data.

    Parameters
    ----------
    df : pd.DataFrame
        Survey DataFrame with columns: region, plan, age, income, usage_hours, satisfaction.

    Returns
    -------
    dict
        Keys: chi2, chi2_p, dof, dependent, corr_strongest_pair, corr_strongest_r
    """
    # --- Chi-square test of independence: region × plan ---
    crosstab = pd.crosstab(df["region"], df["plan"])
    chi2_stat, p_val, dof, _ = chi2_contingency(crosstab)

    # Cast to Python native types to ensure JSON serialisability and type checks
    chi2_stat = float(chi2_stat)
    p_val = float(p_val)
    dof = int(dof)
    dependent = bool(p_val < 0.05)

    # --- Pearson correlation among four numeric columns ---
    numeric_cols = sorted(["age", "income", "usage_hours", "satisfaction"])
    corr_matrix = df[numeric_cols].corr()  # default method="pearson"

    # Collect all unique upper-triangle pairs with their absolute and signed r values
    candidates = []
    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            col_i = numeric_cols[i]
            col_j = numeric_cols[j]
            # numeric_cols is sorted, so i < j means col_i < col_j alphabetically
            r = float(corr_matrix.loc[col_i, col_j])
            candidates.append((abs(r), col_i, col_j, r))

    # Sort: primary key = -abs(r) (highest first), tie-break = col_i asc, col_j asc
    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    _, col_a, col_b, signed_r = candidates[0]

    # The pair is already alphabetically sorted (since numeric_cols was sorted and i<j)
    corr_strongest_pair = [col_a, col_b]
    corr_strongest_r = signed_r

    return {
        "chi2": chi2_stat,
        "chi2_p": p_val,
        "dof": dof,
        "dependent": dependent,
        "corr_strongest_pair": corr_strongest_pair,
        "corr_strongest_r": corr_strongest_r,
    }


def main(argv: list | None = None) -> int:
    """CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>

    Writes results.json, corr_heatmap.png, and region_plan_bar.png into <dir>.
    Returns 0 on success, 1 on error.
    """
    try:
        parser = argparse.ArgumentParser(
            description="Survey correlation and chi-square analysis."
        )
        parser.add_argument("--data", required=True, help="Path to survey CSV file.")
        parser.add_argument(
            "--output-dir", required=True, help="Directory to write outputs."
        )
        args = parser.parse_args(argv)

        # Read data
        df = pd.read_csv(args.data)

        # Run analysis
        results = analyze(df)

        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)

        # --- Write results.json ---
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        # --- Plot 1: Correlation heatmap ---
        numeric_cols = sorted(["age", "income", "usage_hours", "satisfaction"])
        corr_matrix = df[numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(corr_matrix.values, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
        ax.set_yticklabels(numeric_cols)
        plt.colorbar(im, ax=ax, label="Pearson r")
        ax.set_title("Numeric Correlation Heatmap")
        plt.tight_layout()
        heatmap_path = os.path.join(args.output_dir, "corr_heatmap.png")
        plt.savefig(heatmap_path)
        plt.close()

        # --- Plot 2: Region × Plan grouped bar chart ---
        crosstab = pd.crosstab(df["region"], df["plan"])
        fig, ax = plt.subplots(figsize=(7, 5))
        crosstab.plot(kind="bar", ax=ax)
        ax.set_title("Region × Plan Distribution")
        ax.set_xlabel("Region")
        ax.set_ylabel("Count")
        plt.tight_layout()
        bar_path = os.path.join(args.output_dir, "region_plan_bar.png")
        plt.savefig(bar_path)
        plt.close()

        return 0

    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
