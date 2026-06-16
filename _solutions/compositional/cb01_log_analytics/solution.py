"""Gold reference for compositional/cb01_log_analytics — HTTP access-log analytics.

Composes pandas (groupby), numpy (percentile), scipy (zscore), matplotlib,
and json to produce a multi-endpoint latency report.
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
import scipy.stats


def analyze_logs(df: pd.DataFrame) -> dict:
    """Analyse an HTTP access-log DataFrame and return a summary dict.

    Parameters
    ----------
    df : pandas.DataFrame
        Must have columns: endpoint (str), latency_ms (float), status (int).

    Returns
    -------
    dict with keys:
        per_endpoint : dict[str, dict]
            For each endpoint: {"count": int, "p95_latency": float,
                                "error_rate": float}
            where error_rate = fraction of requests with status >= 500.
        slowest_endpoint : str
            Endpoint name with the highest p95_latency.
        anomalies : list[str]
            Endpoints whose p95_latency z-score (across all endpoints) > 2.0.

    Raises
    ------
    ValueError
        If df is empty.
    """
    if df.empty:
        raise ValueError("DataFrame is empty — no logs to analyse")

    per_endpoint: dict[str, dict] = {}

    grouped = df.groupby("endpoint")

    for endpoint, group in grouped:
        count = int(len(group))
        p95 = float(np.percentile(group["latency_ms"].values, 95))
        error_rate = float((group["status"] >= 500).mean())
        per_endpoint[str(endpoint)] = {
            "count": count,
            "p95_latency": p95,
            "error_rate": error_rate,
        }

    # Slowest endpoint by p95
    slowest_endpoint = max(per_endpoint, key=lambda ep: per_endpoint[ep]["p95_latency"])

    # Anomalies: endpoints whose p95 z-score > 2.0
    endpoints = list(per_endpoint.keys())
    p95_values = np.array([per_endpoint[ep]["p95_latency"] for ep in endpoints])

    if len(p95_values) >= 2:
        z_scores = scipy.stats.zscore(p95_values)
        anomalies = [ep for ep, z in zip(endpoints, z_scores) if z > 2.0]
    else:
        anomalies = []

    return {
        "per_endpoint": per_endpoint,
        "slowest_endpoint": slowest_endpoint,
        "anomalies": anomalies,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python solution.py --data <csv_path> --output-dir <dir>."""
    parser = argparse.ArgumentParser(description="HTTP access-log analytics")
    parser.add_argument("--data", required=True, help="Path to the access_log.csv file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze_logs(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write results.json
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    # Bar chart: p95 latency per endpoint
    endpoints = list(results["per_endpoint"].keys())
    p95_vals = [results["per_endpoint"][ep]["p95_latency"] for ep in endpoints]

    fig, ax = plt.subplots(figsize=(max(6, len(endpoints) * 1.2), 5))
    colors = ["tomato" if ep in results["anomalies"] else "steelblue" for ep in endpoints]
    ax.bar(endpoints, p95_vals, color=colors, edgecolor="black", alpha=0.85)
    ax.set_title("P95 Latency by Endpoint")
    ax.set_xlabel("Endpoint")
    ax.set_ylabel("P95 Latency (ms)")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(str(out_dir / "latency.png"), dpi=80)
    plt.close(fig)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
