import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
from scipy import stats


def analyze_logs(df: pd.DataFrame) -> dict:
    """Analyse HTTP access-log DataFrame and return a summary dict.

    Raises ValueError if df is empty.
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    per_endpoint = {}
    for endpoint, group in df.groupby("endpoint"):
        count = int(len(group))
        p95_latency = float(np.percentile(group["latency_ms"], 95))
        error_rate = float((group["status"] >= 500).mean())
        per_endpoint[endpoint] = {
            "count": count,
            "p95_latency": p95_latency,
            "error_rate": error_rate,
        }

    slowest_endpoint = max(per_endpoint, key=lambda e: per_endpoint[e]["p95_latency"])

    endpoints = list(per_endpoint.keys())
    p95_values = np.array([per_endpoint[e]["p95_latency"] for e in endpoints])
    zscores = stats.zscore(p95_values)
    # Guard against NaN (single endpoint or all-equal p95 values → zero std)
    anomalies = [
        e for e, z in zip(endpoints, zscores)
        if not np.isnan(z) and z > 2.0
    ]

    return {
        "per_endpoint": per_endpoint,
        "slowest_endpoint": slowest_endpoint,
        "anomalies": anomalies,
    }


def main(argv=None) -> int:
    """CLI entry point.

    Usage: python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(description="HTTP access-log analytics")
    parser.add_argument("--data", required=True, help="Path to input CSV file")
    parser.add_argument("--output-dir", dest="output_dir", required=True,
                        help="Directory to write results")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        result = analyze_logs(df)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Write results.json
    results_path = os.path.join(output_dir, "results.json")
    with open(results_path, "w") as f:
        json.dump(result, f)

    # Write latency.png — bar chart of p95_latency per endpoint
    per_endpoint = result["per_endpoint"]
    endpoints = list(per_endpoint.keys())
    p95_values = [per_endpoint[e]["p95_latency"] for e in endpoints]

    fig, ax = plt.subplots()
    ax.bar(endpoints, p95_values)
    ax.set_xlabel("Endpoint")
    ax.set_ylabel("p95 Latency (ms)")
    ax.set_title("95th-Percentile Latency per Endpoint")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    latency_path = os.path.join(output_dir, "latency.png")
    plt.savefig(latency_path)
    plt.close(fig)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
