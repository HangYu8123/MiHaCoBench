"""
solution.py — Monthly Sales Trend Analysis (d02_sales_trend)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Perform linear trend, seasonal ANOVA, and price-units correlation analyses."""

    # --- Linear trend of units over time ---
    x = df["month_index"].to_numpy(dtype=float)
    y = df["units"].to_numpy(dtype=float)

    coeffs = np.polyfit(x, y, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    y_hat = np.polyval(coeffs, x)
    SS_res = float(np.sum((y - y_hat) ** 2))
    SS_tot = float(np.sum((y - y.mean()) ** 2))

    # Guard against degenerate case where all units are identical
    if SS_tot == 0:
        r_squared = 1.0
    else:
        r_squared = float(1 - SS_res / SS_tot)

    if slope > 0.1:
        trend_direction = "up"
    elif slope < -0.1:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    # --- Seasonal ANOVA ---
    groups = df.groupby("month_of_year")["units"].apply(list)
    anova_result = scipy.stats.f_oneway(*groups)
    anova_F = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    seasonal_significant = bool(anova_p < 0.05)

    # --- Price–units Pearson correlation ---
    pearson_result = scipy.stats.pearsonr(df["price"], df["units"])
    # Support both scipy >= 1.9 (PearsonRResult) and older scipy (2-tuple)
    try:
        pearson_price_units = float(pearson_result.statistic)
        pearson_p = float(pearson_result.pvalue)
    except AttributeError:
        pearson_price_units = float(pearson_result[0])
        pearson_p = float(pearson_result[1])

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


def main(argv: Optional[list] = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Monthly sales trend analysis")
    parser.add_argument("--data", required=True, help="Path to sales CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(args.data)
    results = analyze(df)

    # Write results.json — all values already Python native types
    with open(os.path.join(output_dir, "results.json"), "w") as f:
        json.dump(results, f)

    # --- Plot 1: trend.png — scatter units vs month_index + polyfit line ---
    x = df["month_index"].to_numpy(dtype=float)
    y = df["units"].to_numpy(dtype=float)
    coeffs = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = np.polyval(coeffs, x_line)

    fig, ax = plt.subplots()
    ax.scatter(x, y, label="Observed units", alpha=0.7)
    ax.plot(x_line, y_line, color="red", label="Trend line")
    ax.set_xlabel("Month Index")
    ax.set_ylabel("Units")
    ax.set_title("Units vs Month Index (Trend)")
    ax.legend()
    fig.savefig(os.path.join(output_dir, "trend.png"))
    plt.close(fig)

    # --- Plot 2: seasonal.png — bar chart of mean units per month_of_year ---
    seasonal_means = df.groupby("month_of_year")["units"].mean()

    fig, ax = plt.subplots()
    ax.bar(seasonal_means.index, seasonal_means.values)
    ax.set_xlabel("Month of Year")
    ax.set_ylabel("Mean Units")
    ax.set_title("Mean Units by Month of Year (Seasonal Profile)")
    fig.savefig(os.path.join(output_dir, "seasonal.png"))
    plt.close(fig)

    # --- Plot 3: correlation.png — scatter price vs units ---
    fig, ax = plt.subplots()
    ax.scatter(df["price"], df["units"], alpha=0.7)
    ax.set_xlabel("Price")
    ax.set_ylabel("Units")
    ax.set_title("Price vs Units")
    fig.savefig(os.path.join(output_dir, "correlation.png"))
    plt.close(fig)

    return 0


if __name__ == "__main__":
    sys.exit(main())
