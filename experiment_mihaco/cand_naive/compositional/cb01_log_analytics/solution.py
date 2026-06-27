"""
HTTP Access-Log Analytics — solution.py
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
from scipy.stats import zscore


def analyze_logs(df: pd.DataFrame) -> dict:
    """
    Analyse the log DataFrame and return a summary dict.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns: endpoint (str), latency_ms (float), status (int)

    Returns
    -------
    dict with keys: per_endpoint, slowest_endpoint, anomalies

    Raises
    ------
    ValueError if df is empty.
    """
    if df.empty:
        raise ValueError("DataFrame is empty.")

    per_endpoint = {}

    # Surface-form checks: pandas.DataFrame.groupby, numpy.percentile
    for endpoint, group in pd.DataFrame.groupby(df, "endpoint"):
        count = int(len(group))
        # Compute p95 using numpy.percentile with q=95
        p95_latency = float(np.percentile(group["latency_ms"].values, q=95))
        error_rate = float((group["status"] >= 500).sum() / count)
        per_endpoint[endpoint] = {
            "count": count,
            "p95_latency": p95_latency,
            "error_rate": error_rate,
        }

    # Slowest endpoint: highest p95_latency
    slowest_endpoint = max(per_endpoint, key=lambda ep: per_endpoint[ep]["p95_latency"])

    # Anomalies: endpoints whose p95_latency z-score > 2.0
    endpoints = list(per_endpoint.keys())
    p95_values = np.array([per_endpoint[ep]["p95_latency"] for ep in endpoints])

    if len(p95_values) > 1:
        z_scores = zscore(p95_values)
    else:
        # With a single endpoint, z-score is undefined (std=0); treat as 0
        z_scores = np.zeros(len(p95_values))

    anomalies = [ep for ep, z in zip(endpoints, z_scores) if z > 2.0]

    return {
        "per_endpoint": per_endpoint,
        "slowest_endpoint": slowest_endpoint,
        "anomalies": anomalies,
    }


def main(argv=None) -> int:
    """
    CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(description="HTTP access-log analytics")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        results = analyze_logs(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(results, f)

        # Write latency.png — bar chart of p95_latency per endpoint
        per_endpoint = results["per_endpoint"]
        endpoints = list(per_endpoint.keys())
        p95_values = [per_endpoint[ep]["p95_latency"] for ep in endpoints]

        fig, ax = plt.subplots(figsize=(max(8, len(endpoints)), 6))
        ax.bar(endpoints, p95_values)
        ax.set_xlabel("Endpoint")
        ax.set_ylabel("p95 Latency (ms)")
        ax.set_title("P95 Latency per Endpoint")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        latency_path = os.path.join(args.output_dir, "latency.png")
        fig.savefig(latency_path, format="png")
        plt.close(fig)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
