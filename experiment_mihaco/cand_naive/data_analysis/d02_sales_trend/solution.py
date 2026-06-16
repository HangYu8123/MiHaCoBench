"""solution.py — Monthly Sales Trend Analysis."""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, pearsonr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def analyze(df: pd.DataFrame) -> dict:
    """Perform three analyses on the dataframe and return a dict with nine keys."""

    # --- Linear trend of units over time ---
    x = df["month_index"].to_numpy(dtype=float)
    y = df["units"].to_numpy(dtype=float)

    coeffs = np.polyfit(x, y, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    y_pred = np.polyval(coeffs, x)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot != 0.0 else 0.0

    if slope > 0.1:
        trend_direction = "up"
    elif slope < -0.1:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    # --- Seasonal ANOVA ---
    groups = [
        df.loc[df["month_of_year"] == m, "units"].to_numpy(dtype=float)
        for m in range(12)
        if (df["month_of_year"] == m).any()
    ]
    f_stat, p_val = f_oneway(*groups)
    anova_F = float(f_stat)
    anova_p = float(p_val)
    seasonal_significant = bool(anova_p < 0.05)

    # --- Price–units correlation ---
    price = df["price"].to_numpy(dtype=float)
    units = df["units"].to_numpy(dtype=float)
    r_val, p_pearson = pearsonr(price, units)
    pearson_price_units = float(r_val)
    pearson_p = float(p_pearson)

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


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Monthly sales trend analysis")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
    except Exception as exc:
        print(f"Error reading CSV: {exc}", file=sys.stderr)
        return 1

    results = analyze(df)

    os.makedirs(args.output_dir, exist_ok=True)

    # Write results.json
    results_path = os.path.join(args.output_dir, "results.json")
    with open(results_path, "w") as fh:
        json.dump(results, fh)

    # --- Plot 1: units vs month_index with trend line ---
    x = df["month_index"].to_numpy(dtype=float)
    y_units = df["units"].to_numpy(dtype=float)
    coeffs = np.polyfit(x, y_units, 1)
    trend_line = np.polyval(coeffs, x)

    fig, ax = plt.subplots()
    ax.scatter(x, y_units, label="units", alpha=0.7)
    ax.plot(x, trend_line, color="red", label="trend line")
    ax.set_xlabel("month_index")
    ax.set_ylabel("units")
    ax.set_title("Units vs Month Index with Trend Line")
    ax.legend()
    fig.savefig(os.path.join(args.output_dir, "units_trend.png"))
    plt.close(fig)

    # --- Plot 2: mean units per month_of_year (seasonal profile) ---
    seasonal_mean = df.groupby("month_of_year")["units"].mean()

    fig, ax = plt.subplots()
    ax.bar(seasonal_mean.index, seasonal_mean.values)
    ax.set_xlabel("month_of_year")
    ax.set_ylabel("mean units")
    ax.set_title("Mean Units per Month of Year (Seasonal Profile)")
    fig.savefig(os.path.join(args.output_dir, "seasonal_profile.png"))
    plt.close(fig)

    # --- Plot 3: price vs units ---
    price = df["price"].to_numpy(dtype=float)

    fig, ax = plt.subplots()
    ax.scatter(price, y_units, alpha=0.7)
    ax.set_xlabel("price")
    ax.set_ylabel("units")
    ax.set_title("Price vs Units")
    fig.savefig(os.path.join(args.output_dir, "price_vs_units.png"))
    plt.close(fig)

    return 0


if __name__ == "__main__":
    sys.exit(main())
