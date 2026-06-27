"""
cb01_log_analytics — HTTP Access-Log Analytics
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import argparse
import json
import os
import sys

import numpy
import pandas
import scipy.stats


def analyze_logs(df: pandas.DataFrame) -> dict:
    """
    Analyse the log DataFrame and return a summary dict.

    Raises ValueError if df is empty.

    Returns a dict with keys:
        per_endpoint : dict  — per-endpoint statistics
        slowest_endpoint : str  — endpoint with highest p95_latency
        anomalies : list[str]  — endpoints with p95 z-score > 2.0
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    per_endpoint = {}

    for endpoint_name, group in df.groupby("endpoint"):
        count = int(len(group))
        p95_latency = float(numpy.percentile(group["latency_ms"].values, 95))
        error_rate = float((group["status"] >= 500).mean())

        per_endpoint[endpoint_name] = {
            "count": count,
            "p95_latency": p95_latency,
            "error_rate": error_rate,
        }

    # Slowest endpoint: the one with the highest p95_latency
    slowest_endpoint = max(per_endpoint, key=lambda e: per_endpoint[e]["p95_latency"])

    # Anomalies: endpoints whose p95 z-score > 2.0
    endpoint_names = list(per_endpoint.keys())
    p95_array = numpy.array([per_endpoint[e]["p95_latency"] for e in endpoint_names])

    if len(p95_array) > 1:
        zscores = scipy.stats.zscore(p95_array)
        # Guard against NaN (e.g., all-equal values -> std=0)
        zscores = numpy.nan_to_num(zscores, nan=0.0)
    else:
        # Single endpoint: z-score is undefined/0 — no anomalies
        zscores = numpy.zeros(len(p95_array))

    anomalies = [endpoint_names[i] for i in range(len(endpoint_names)) if zscores[i] > 2.0]

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

    Reads CSV, calls analyze_logs, writes results.json and latency.png.
    Returns 0 on success, non-zero on error.
    """
    parser = argparse.ArgumentParser(description="HTTP Access-Log Analytics")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)

        # Read CSV
        df = pandas.read_csv(args.data)

        # Analyse logs
        result = analyze_logs(df)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result, f)

        # Build bar chart of p95_latency per endpoint and save latency.png
        per_endpoint = result["per_endpoint"]
        endpoint_names = list(per_endpoint.keys())
        p95_values = [per_endpoint[e]["p95_latency"] for e in endpoint_names]

        fig, ax = plt.subplots()
        ax.bar(endpoint_names, p95_values)
        ax.set_xlabel("Endpoint")
        ax.set_ylabel("P95 Latency (ms)")
        ax.set_title("P95 Latency per Endpoint")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        latency_path = os.path.join(args.output_dir, "latency.png")
        plt.savefig(latency_path)
        plt.close(fig)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
