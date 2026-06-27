"""
Solution for d04_survey_correlation: Categorical Dependence & Numeric Correlation.
"""
import argparse
import itertools
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import chi2_contingency


def analyze(df: pd.DataFrame) -> dict:
    """Perform chi-square and Pearson correlation analyses on survey data.

    Parameters
    ----------
    df : pd.DataFrame
        Survey data with columns: region, plan, age, income, usage_hours, satisfaction.

    Returns
    -------
    dict
        Keys: chi2, chi2_p, dof, dependent, corr_strongest_pair, corr_strongest_r.
    """
    # --- Chi-square test of independence: region x plan ---
    ct = pd.crosstab(df["region"], df["plan"])
    chi2_raw, p_raw, dof_raw, _ = chi2_contingency(ct)

    chi2 = float(chi2_raw)
    chi2_p = float(p_raw)
    dof = int(dof_raw)
    dependent = bool(chi2_p < 0.05)

    # --- Pearson correlation matrix ---
    numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
    corr = df[numeric_cols].corr()

    # Find the pair with highest absolute Pearson r.
    # Tie-break: first column name alphabetically, then second column name.
    # Store pairs in alphabetical order (name1 < name2) for consistency.
    candidates = []
    for col_a, col_b in itertools.combinations(numeric_cols, 2):
        name1 = min(col_a, col_b)
        name2 = max(col_a, col_b)
        abs_r = abs(corr.loc[name1, name2])
        candidates.append((-abs_r, name1, name2))

    # Sort by (-abs_r, name1, name2) — first element is negative abs_r for descending sort
    candidates.sort()
    _, name1, name2 = candidates[0]

    corr_strongest_pair = [name1, name2]
    corr_strongest_r = float(corr.loc[name1, name2])

    return {
        "chi2": chi2,
        "chi2_p": chi2_p,
        "dof": dof,
        "dependent": dependent,
        "corr_strongest_pair": corr_strongest_pair,
        "corr_strongest_r": corr_strongest_r,
    }


def main(argv=None) -> int:
    """CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(
        description="Survey correlation analysis: chi-square and Pearson r."
    )
    parser.add_argument("--data", required=True, help="Path to the survey CSV file.")
    parser.add_argument(
        "--output-dir", required=True, dest="output_dir",
        help="Directory to write outputs (results.json and PNG files)."
    )
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        # --- Plot 1: Correlation heatmap ---
        numeric_cols = ["age", "income", "usage_hours", "satisfaction"]
        corr = df[numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm")
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_yticklabels(numeric_cols)
        fig.colorbar(im, ax=ax)
        ax.set_title("Pearson Correlation Heatmap")
        heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
        fig.savefig(heatmap_path, bbox_inches="tight")
        plt.close(fig)

        # --- Plot 2: Region x Plan grouped bar chart ---
        ct = pd.crosstab(df["region"], df["plan"])
        fig, ax = plt.subplots(figsize=(7, 5))
        ct.plot(kind="bar", ax=ax)
        ax.set_title("Region × Plan Distribution")
        ax.set_xlabel("Region")
        ax.set_ylabel("Count")
        ax.legend(title="Plan")
        plt.xticks(rotation=0)
        barchart_path = os.path.join(output_dir, "region_plan_barchart.png")
        fig.savefig(barchart_path, bbox_inches="tight")
        plt.close(fig)

        return 0

    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
