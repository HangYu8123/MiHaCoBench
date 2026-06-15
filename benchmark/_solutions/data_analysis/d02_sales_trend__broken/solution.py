"""Deliberately-broken reference for data_analysis/d02_sales_trend.

Planted defects (two bugs, either will trigger grader failure):
  1. r_squared is computed incorrectly: uses (1 - SS_res/SS_tot) but with
     SS_tot computed as sum of squared PREDICTED values instead of deviations
     from the mean.  This gives a wrong r_squared value.
  2. trend_direction is derived from the SIGN OF THE INTERCEPT rather than
     the slope, so it can produce 'up', 'down', or 'flat' incorrectly
     (the intercept is ~324 which is positive -> 'up' accidentally matches;
     but r_squared will be wrong so the numeric test fails).

These defects ensure >=1 grader test fails on this broken variant.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import f_oneway, pearsonr


def analyze(df: pd.DataFrame) -> dict:
    """Analyze sales data (broken variant with planted defects)."""
    x = df["month_index"].to_numpy(dtype=float)
    y = df["units"].to_numpy(dtype=float)

    coeffs = np.polyfit(x, y, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    y_pred = slope * x + intercept
    ss_res = float(np.sum((y - y_pred) ** 2))
    # BUG 1: Wrong SS_tot — uses sum of squared predicted values instead of
    # deviations from mean.  Produces a wildly wrong r_squared.
    ss_tot_wrong = float(np.sum(y_pred ** 2))
    r_squared = 1.0 - ss_res / ss_tot_wrong  # WRONG

    # BUG 2: trend_direction from intercept sign, not slope sign.
    if intercept > 0.1:
        trend_direction = "up"
    elif intercept < -0.1:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    groups = [
        df.loc[df["month_of_year"] == m, "units"].to_numpy(dtype=float)
        for m in sorted(df["month_of_year"].unique())
    ]
    anova_result = f_oneway(*groups)
    anova_F = float(anova_result.statistic)
    anova_p = float(anova_result.pvalue)
    seasonal_significant = anova_p < 0.05

    price = df["price"].to_numpy(dtype=float)
    pearson_result = pearsonr(price, y)
    pearson_price_units = float(pearson_result.statistic)
    pearson_p = float(pearson_result.pvalue)

    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,       # WRONG value
        "trend_direction": trend_direction,  # wrong logic (happens to be 'up' here)
        "anova_F": anova_F,
        "anova_p": anova_p,
        "seasonal_significant": seasonal_significant,
        "pearson_price_units": pearson_price_units,
        "pearson_p": pearson_p,
    }


def _save_plots(df: pd.DataFrame, results: dict, output_dir: Path) -> None:
    """Save the required PNG plots to output_dir."""
    x = df["month_index"].to_numpy(dtype=float)
    y = df["units"].to_numpy(dtype=float)
    slope = results["slope"]
    intercept = results["intercept"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(x, y, color="steelblue", alpha=0.7, label="units")
    x_line = np.linspace(x.min(), x.max(), 200)
    ax.plot(x_line, slope * x_line + intercept, color="red", linewidth=2, label="trend")
    ax.set_xlabel("month_index")
    ax.set_ylabel("units")
    ax.set_title("Units vs Month Index with Trend Line")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "scatter_trend.png")
    plt.close(fig)

    seasonal_means = df.groupby("month_of_year")["units"].mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(seasonal_means.index, seasonal_means.values, color="steelblue")
    ax.set_xlabel("month_of_year")
    ax.set_ylabel("mean units")
    ax.set_title("Seasonal Mean Units by Month of Year")
    fig.tight_layout()
    fig.savefig(output_dir / "seasonal_means.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(y, df["price"].to_numpy(dtype=float), color="darkorange", alpha=0.7)
    ax.set_xlabel("units")
    ax.set_ylabel("price")
    ax.set_title("Price vs Units")
    fig.tight_layout()
    fig.savefig(output_dir / "price_vs_units.png")
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: --data <csv_path> --output-dir <dir>."""
    parser = argparse.ArgumentParser(description="Sales trend analysis")
    parser.add_argument("--data", required=True, help="Path to sales.csv")
    parser.add_argument("--output-dir", required=True, help="Directory to write results")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "results.json").write_text(json.dumps(results, indent=2))
    _save_plots(df, results, out_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
