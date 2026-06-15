"""Deliberately-broken reference for data_analysis/d03_customer_segments.

Planted defect: selects best_k by MINIMUM inertia instead of maximum silhouette.
Since inertia always decreases as k increases, this always picks k=6.
This fails test_best_k_is_four (expects 4, gets 6) and related tests.
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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def analyze(df: pd.DataFrame) -> dict:
    """Cluster customers using KMeans.

    BUG: selects best_k by minimum inertia (always k=6) instead of
    maximum silhouette score.
    """
    features = df[["recency", "frequency", "monetary"]].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    inertia_by_k: dict[str, float] = {}
    sil_scores: dict[int, float] = {}

    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia_by_k[str(k)] = float(km.inertia_)
        sil = silhouette_score(X_scaled, labels)
        sil_scores[k] = float(sil)

    # BUG: pick best_k by MINIMUM inertia (always k=6), not max silhouette
    best_k = int(min(inertia_by_k, key=lambda k: inertia_by_k[k]))
    # best_sil is still computed from the sil_scores dict at best_k
    best_sil = float(sil_scores[best_k])

    km_best = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    best_labels = km_best.fit_predict(X_scaled)

    unique, counts = np.unique(best_labels, return_counts=True)
    cluster_sizes = sorted(counts.tolist(), reverse=True)

    return {
        "best_k": best_k,
        "silhouette": best_sil,
        "inertia_by_k": inertia_by_k,
        "cluster_sizes": cluster_sizes,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python solution.py --data <csv> --output-dir <dir>."""
    parser = argparse.ArgumentParser(description="Customer segmentation via KMeans")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    features = df[["recency", "frequency", "monetary"]].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)
    best_k = results["best_k"]
    km_best = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    best_labels = km_best.fit_predict(X_scaled)

    ks = [int(k) for k in sorted(results["inertia_by_k"].keys(), key=int)]
    inertias = [results["inertia_by_k"][str(k)] for k in ks]
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(ks, inertias, marker="o", color="steelblue")
    ax1.set_title("Elbow Curve")
    fig1.tight_layout()
    fig1.savefig(str(out_dir / "elbow_inertia.png"), dpi=80)
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    sil_vals: dict[int, float] = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil_vals[k] = float(silhouette_score(X_scaled, labels))
    ax2.plot(list(sil_vals.keys()), list(sil_vals.values()), marker="s", color="darkorange")
    ax2.set_title("Silhouette Score vs k")
    fig2.tight_layout()
    fig2.savefig(str(out_dir / "silhouette_scores.png"), dpi=80)
    plt.close(fig2)

    pca = PCA(n_components=2, random_state=0)
    X_2d = pca.fit_transform(X_scaled)
    fig3, ax3 = plt.subplots(figsize=(7, 5))
    scatter = ax3.scatter(X_2d[:, 0], X_2d[:, 1], c=best_labels, cmap="tab10", alpha=0.7, s=20)
    plt.colorbar(scatter, ax=ax3, label="Cluster")
    ax3.set_title(f"PCA Scatter (k={best_k})")
    fig3.tight_layout()
    fig3.savefig(str(out_dir / "pca_scatter.png"), dpi=80)
    plt.close(fig3)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
