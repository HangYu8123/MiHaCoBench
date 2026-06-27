"""
solution.py — Monthly Sales Trend Analysis (d02_sales_trend)

Public contract:
    analyze(df: pandas.DataFrame) -> dict
    main(argv: list[str] | None = None) -> int
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
from scipy.stats import f_oneway, pearsonr


def analyze(df: pd.DataFrame) -> dict:
    """Perform three statistical analyses on the sales dataframe.

    Returns a dict with exactly 9 keys:
        slope, intercept, r_squared, trend_direction,
        anova_F, anova_p, seasonal_significant,
        pearson_price_units, pearson_p
    """
    # --- 1. Linear trend: units vs month_index ---
    x = df["month_index"].values.astype(float)
    y = df["units"].values.astype(float)

    coeffs = np.polyfit(x, y, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    y_hat = slope * x + intercept
    y_mean = float(np.mean(y))
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y_mean) ** 2))
    r_squared = float(1.0 - ss_res / ss_tot) if ss_tot != 0.0 else 0.0

    if slope > 0.1:
        trend_direction = "up"
    elif slope < -0.1:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    # --- 2. Seasonal ANOVA: units grouped by month_of_year ---
    groups = [g.values for _, g in df.groupby("month_of_year")["units"]]
    anova_result = f_oneway(*groups)
    anova_F = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    seasonal_significant = bool(anova_p < 0.05)

    # --- 3. Price–units Pearson correlation ---
    pr_result = pearsonr(df["price"].values.astype(float),
                         df["units"].values.astype(float))
    pearson_price_units = float(pr_result[0])
    pearson_p = float(pr_result[1])

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
    """CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>

    Writes results.json, trend.png, seasonal.png, price_units.png to <dir>.
    Returns 0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(description="Monthly sales trend analysis")
    parser.add_argument("--data", required=True, help="Path to CSV data file")
    parser.add_argument("--output-dir", dest="output_dir", required=True,
                        help="Directory to write output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)

        result = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result, f)

        slope = result["slope"]
        intercept = result["intercept"]
        x = df["month_index"].values.astype(float)
        y = df["units"].values.astype(float)

        # Plot 1: trend.png — scatter of units vs month_index with trend line
        fig, ax = plt.subplots()
        ax.scatter(x, y, label="Observed", alpha=0.7)
        x_line = np.array([x.min(), x.max()])
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color="red", label="Trend")
        ax.set_xlabel("month_index")
        ax.set_ylabel("units")
        ax.set_title("Units vs Month Index (with trend line)")
        ax.legend()
        plt.savefig(os.path.join(args.output_dir, "trend.png"))
        plt.close()

        # Plot 2: seasonal.png — bar chart of mean units per month_of_year
        monthly_mean = df.groupby("month_of_year")["units"].mean()
        fig, ax = plt.subplots()
        ax.bar(monthly_mean.index, monthly_mean.values)
        ax.set_xlabel("month_of_year")
        ax.set_ylabel("mean units")
        ax.set_title("Mean Units per Month of Year (Seasonal Profile)")
        plt.savefig(os.path.join(args.output_dir, "seasonal.png"))
        plt.close()

        # Plot 3: price_units.png — scatter of price vs units
        fig, ax = plt.subplots()
        ax.scatter(df["price"].values, df["units"].values, alpha=0.7)
        ax.set_xlabel("price")
        ax.set_ylabel("units")
        ax.set_title("Price vs Units")
        plt.savefig(os.path.join(args.output_dir, "price_units.png"))
        plt.close()

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
