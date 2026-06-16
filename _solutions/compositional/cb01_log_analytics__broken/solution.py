"""BROKEN reference for compositional/cb01_log_analytics.

PLANTED DEFECT (localized): Uses MEAN latency instead of 95th percentile
for p95_latency computation. This causes:
  - per_endpoint[ep]["p95_latency"]  wrong (mean, not p95)
  - slowest_endpoint  may differ (mean order != p95 order)
  - anomalies  wrong (z-scores computed from means, not p95s)

Everything else (counts, error_rate) remains correct.
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
        slowest_endpoint : str
        anomalies : list[str]

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
        # BUG: computes MEAN instead of 95th percentile
        p95 = float(np.mean(group["latency_ms"].values))
        error_rate = float((group["status"] >= 500).mean())
        per_endpoint[str(endpoint)] = {
            "count": count,
            "p95_latency": p95,
            "error_rate": error_rate,
        }

    # Slowest endpoint by (incorrect) "p95"
    slowest_endpoint = max(per_endpoint, key=lambda ep: per_endpoint[ep]["p95_latency"])

    # Anomalies: endpoints whose "p95" z-score > 2.0 (computed from means)
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

    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    endpoints = list(results["per_endpoint"].keys())
    p95_vals = [results["per_endpoint"][ep]["p95_latency"] for ep in endpoints]

    fig, ax = plt.subplots(figsize=(max(6, len(endpoints) * 1.2), 5))
    colors = ["tomato" if ep in results["anomalies"] else "steelblue" for ep in endpoints]
    ax.bar(endpoints, p95_vals, color=colors, edgecolor="black", alpha=0.85)
    ax.set_title("Mean Latency by Endpoint (broken)")
    ax.set_xlabel("Endpoint")
    ax.set_ylabel("Latency (ms)")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(str(out_dir / "latency.png"), dpi=80)
    plt.close(fig)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
