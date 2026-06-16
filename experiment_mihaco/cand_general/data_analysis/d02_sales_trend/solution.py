"""
solution.py — Monthly Sales Trend Analysis (d02_sales_trend)

Public contract:
  analyze(df) -> dict   (9 keys)
  main(argv=None) -> int
"""

import argparse
import json
import os
import sys

import numpy
import pandas
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats


def analyze(df: pandas.DataFrame) -> dict:
    """Perform three analyses on the dataframe and return a dict with exactly 9 keys."""

    # --- 1. Linear trend of units over time ---
    x = df['month_index'].values
    y = df['units'].values

    coeffs = numpy.polyfit(x, y, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    y_hat = slope * x + intercept
    ss_res = numpy.sum((y - y_hat) ** 2)
    ss_tot = numpy.sum((y - y.mean()) ** 2)
    r_squared = float(1 - ss_res / ss_tot)

    if slope > 0.1:
        trend_direction = "up"
    elif slope < -0.1:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    # --- 2. Seasonal ANOVA ---
    groups = [grp['units'].values for _, grp in df.groupby('month_of_year', sort=True)]
    F, p = stats.f_oneway(*groups)
    anova_F = float(F)
    anova_p = float(p)
    seasonal_significant = bool(anova_p < 0.05)

    # --- 3. Price-units Pearson correlation ---
    r, pval = stats.pearsonr(df['price'].values, df['units'].values)
    pearson_price_units = float(r)
    pearson_p = float(pval)

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'trend_direction': trend_direction,
        'anova_F': anova_F,
        'anova_p': anova_p,
        'seasonal_significant': seasonal_significant,
        'pearson_price_units': pearson_price_units,
        'pearson_p': pearson_p,
    }


def main(argv=None) -> int:
    """CLI entry point."""
    try:
        parser = argparse.ArgumentParser(description='Monthly Sales Trend Analysis')
        parser.add_argument('--data', required=True, help='Path to CSV data file')
        parser.add_argument('--output-dir', required=True, help='Directory to write outputs')
        args = parser.parse_args(argv)

        df = pandas.read_csv(args.data)
        results = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        json_path = os.path.join(args.output_dir, 'results.json')
        with open(json_path, 'w') as f:
            f.write(json.dumps(results))

        x = df['month_index'].values
        y = df['units'].values
        slope = results['slope']
        intercept = results['intercept']

        # Plot 1: Scatter of units vs month_index with trend line
        plt.figure()
        plt.scatter(x, y, label='Observed', alpha=0.7)
        x_line = numpy.array([x.min(), x.max()])
        plt.plot(x_line, slope * x_line + intercept, color='red', label='Trend line')
        plt.xlabel('Month Index')
        plt.ylabel('Units Sold')
        plt.title('Units vs Month Index (Linear Trend)')
        plt.legend()
        plt.savefig(os.path.join(args.output_dir, 'trend.png'))
        plt.close()

        # Plot 2: Bar chart of mean units per month_of_year
        plt.figure()
        seasonal_means = df.groupby('month_of_year')['units'].mean()
        plt.bar(seasonal_means.index, seasonal_means.values)
        plt.xlabel('Month of Year')
        plt.ylabel('Mean Units Sold')
        plt.title('Seasonal Profile: Mean Units per Month')
        plt.savefig(os.path.join(args.output_dir, 'seasonal.png'))
        plt.close()

        # Plot 3: Scatter of price vs units
        plt.figure()
        plt.scatter(df['price'].values, df['units'].values, alpha=0.7)
        plt.xlabel('Price')
        plt.ylabel('Units Sold')
        plt.title('Price vs Units (Pearson r = {:.3f})'.format(results['pearson_price_units']))
        plt.savefig(os.path.join(args.output_dir, 'correlation.png'))
        plt.close()

        return 0

    except Exception:
        return 1


if __name__ == '__main__':
    sys.exit(main())
