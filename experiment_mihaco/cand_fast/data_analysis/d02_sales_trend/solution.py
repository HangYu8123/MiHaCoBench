"""
Data Analysis 02 — sales_trend: Monthly Sales Trend Analysis
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import f_oneway, pearsonr


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform three analyses on the dataframe and return a dict with exactly 9 keys.
    """
    # --- Linear trend of units over time ---
    x = df["month_index"].values
    y = df["units"].values

    coeffs = np.polyfit(x, y, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    # Compute R² manually
    y_pred = np.polyval(coeffs, x)
    SS_res = float(np.sum((y - y_pred) ** 2))
    SS_tot = float(np.sum((y - y.mean()) ** 2))
    if SS_tot == 0:
        r_squared = 1.0
    else:
        r_squared = float(1.0 - SS_res / SS_tot)

    # trend_direction: strict inequalities
    if slope > 0.1:
        trend_direction = "up"
    elif slope < -0.1:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    # --- Seasonal ANOVA ---
    groups = [g["units"].values for _, g in df.groupby("month_of_year")]
    f_stat, anova_p_val = f_oneway(*groups)
    anova_F = float(f_stat)
    anova_p = float(anova_p_val)
    seasonal_significant = bool(anova_p < 0.05)

    # --- Price–units correlation ---
    r_val, p_val = pearsonr(df["price"].values, df["units"].values)
    pearson_price_units = float(r_val)
    pearson_p = float(p_val)

    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "trend_direction": trend_direction,
        "anova_F": anova_F,
        "anova_p": anova_p,
        "seasonal_significant": seasonal_significant,
        "pearson_price_units": pearson_price_units,
        "pearson_p": pearson_p,
    }


def main(argv=None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Monthly Sales Trend Analysis"
    )
    parser.add_argument("--data", required=True, help="Path to sales CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory for results")
    args = parser.parse_args(argv)

    # Read data
    df = pd.read_csv(args.data)

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run analysis
    results = analyze(df)

    # Write results.json
    results_path = output_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(results, f)

    # --- Plot 1: Scatter of units vs month_index with trend line ---
    x = df["month_index"].values
    y = df["units"].values
    coeffs = np.polyfit(x, y, 1)

    fig, ax = plt.subplots()
    ax.scatter(x, y, label="units", alpha=0.7)
    ax.plot(x, np.polyval(coeffs, x), color="red", label="trend line")
    ax.set_xlabel("month_index")
    ax.set_ylabel("units")
    ax.set_title("Units vs Month Index with Trend Line")
    ax.legend()
    fig.savefig(output_dir / "units_vs_month_index.png")
    plt.close(fig)

    # --- Plot 2: Bar chart of mean units per month_of_year ---
    monthly_mean = df.groupby("month_of_year")["units"].mean()
    months = monthly_mean.index.values
    means = monthly_mean.values

    fig, ax = plt.subplots()
    ax.bar(months, means)
    ax.set_xlabel("month_of_year")
    ax.set_ylabel("mean units")
    ax.set_title("Mean Units per Month of Year (Seasonal Profile)")
    fig.savefig(output_dir / "seasonal_profile.png")
    plt.close(fig)

    # --- Plot 3: Scatter of price vs units ---
    fig, ax = plt.subplots()
    ax.scatter(df["price"].values, df["units"].values, alpha=0.7)
    ax.set_xlabel("price")
    ax.set_ylabel("units")
    ax.set_title("Price vs Units")
    fig.savefig(output_dir / "price_vs_units.png")
    plt.close(fig)

    return 0


if __name__ == "__main__":
    sys.exit(main())
