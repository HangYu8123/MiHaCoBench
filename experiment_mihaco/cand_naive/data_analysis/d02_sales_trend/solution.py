"""
solution.py — Monthly Sales Trend Analysis (d02_sales_trend)
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
    """Perform three analyses on the dataframe and return a dict with exactly nine keys."""

    # --- 1. Linear trend of units over time ---
    x = df["month_index"].to_numpy(dtype=float)
    y = df["units"].to_numpy(dtype=float)

    coeffs = np.polyfit(x, y, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    # R² = 1 - SS_res / SS_tot
    y_pred = slope * x + intercept
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0

    if slope > 0.1:
        trend_direction = "up"
    elif slope < -0.1:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    # --- 2. Seasonal ANOVA ---
    groups = [
        df.loc[df["month_of_year"] == m, "units"].to_numpy(dtype=float)
        for m in sorted(df["month_of_year"].unique())
    ]
    f_stat, p_val = f_oneway(*groups)
    anova_F = float(f_stat)
    anova_p = float(p_val)
    seasonal_significant = bool(anova_p < 0.05)

    # --- 3. Price–units correlation ---
    price = df["price"].to_numpy(dtype=float)
    units_arr = df["units"].to_numpy(dtype=float)
    r_val, p_pearson = pearsonr(price, units_arr)
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
    parser = argparse.ArgumentParser(description="Monthly Sales Trend Analysis")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory to write outputs")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze(df)

        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write results.json
        with open(out_dir / "results.json", "w") as f:
            json.dump(results, f)

        # --- Plot 1: units vs month_index with trend line ---
        x = df["month_index"].to_numpy(dtype=float)
        y = df["units"].to_numpy(dtype=float)
        slope = results["slope"]
        intercept = results["intercept"]
        y_line = slope * x + intercept

        fig, ax = plt.subplots()
        ax.scatter(x, y, label="Observed units", alpha=0.7)
        ax.plot(x, y_line, color="red", label=f"Trend (slope={slope:.2f})")
        ax.set_xlabel("Month Index")
        ax.set_ylabel("Units")
        ax.set_title("Units vs Month Index with Trend Line")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / "trend_units.png")
        plt.close(fig)

        # --- Plot 2: bar chart of mean units per month_of_year ---
        monthly_mean = df.groupby("month_of_year")["units"].mean()
        fig, ax = plt.subplots()
        ax.bar(monthly_mean.index, monthly_mean.values, color="steelblue")
        ax.set_xlabel("Month of Year (0=Jan)")
        ax.set_ylabel("Mean Units")
        ax.set_title("Seasonal Profile: Mean Units per Month")
        ax.set_xticks(range(12))
        fig.tight_layout()
        fig.savefig(out_dir / "seasonal_profile.png")
        plt.close(fig)

        # --- Plot 3: price vs units scatter ---
        fig, ax = plt.subplots()
        ax.scatter(df["price"], df["units"], alpha=0.7, color="green")
        ax.set_xlabel("Price")
        ax.set_ylabel("Units")
        ax.set_title("Price vs Units")
        fig.tight_layout()
        fig.savefig(out_dir / "price_vs_units.png")
        plt.close(fig)

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
