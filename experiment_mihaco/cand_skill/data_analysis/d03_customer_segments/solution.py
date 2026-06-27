"""
solution.py — KMeans Customer Segmentation
Data Analysis 03: customer_segments
"""

import sys
import json
import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform KMeans customer segmentation.

    Returns a dict with keys:
        best_k         (int)   — k with the highest silhouette score
        silhouette     (float) — silhouette score for best_k
        inertia_by_k   (dict)  — {str(k): float} for k in 2..6
        cluster_sizes  (list)  — cluster membership counts sorted descending
    """
    # Step 1: Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[["recency", "frequency", "monetary"]])

    # Step 2 & 3: Fit KMeans and compute silhouette for each k
    ks = range(2, 7)  # k in {2, 3, 4, 5, 6}
    inertia_by_k = {}
    silhouette_by_k = {}

    for k in ks:
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia_by_k[str(k)] = float(km.inertia_)
        silhouette_by_k[k] = float(silhouette_score(X_scaled, labels))

    # Step 4: Choose best_k as the k with the highest silhouette score
    best_k = int(max(silhouette_by_k, key=silhouette_by_k.get))
    best_silhouette = silhouette_by_k[best_k]  # use stored value, NOT recomputed

    # Step 5: Refit KMeans with best_k to obtain final cluster labels
    km_best = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    best_labels = km_best.fit_predict(X_scaled)

    # cluster_sizes sorted descending
    cluster_sizes = sorted(Counter(best_labels.tolist()).values(), reverse=True)

    return {
        "best_k": best_k,
        "silhouette": best_silhouette,
        "inertia_by_k": inertia_by_k,
        "cluster_sizes": list(cluster_sizes),
    }


def main(argv: list = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="KMeans customer segmentation")
    parser.add_argument("--data", required=True, help="Path to customers CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory to write outputs")
    args = parser.parse_args(argv)

    try:
        # Read CSV
        df = pd.read_csv(args.data)

        # Call analyze
        results = analyze(df)

        # Ensure output directory exists
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write results.json
        results_path = output_dir / "results.json"
        with open(results_path, "w") as f:
            json.dump(results, f)

        # Prepare data for plots
        ks = list(range(2, 7))
        inertias = [results["inertia_by_k"][str(k)] for k in ks]

        # Re-run to get silhouette scores for plotting
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[["recency", "frequency", "monetary"]])
        sil_scores = []
        for k in ks:
            km = KMeans(n_clusters=k, random_state=0, n_init=10)
            labels = km.fit_predict(X_scaled)
            sil_scores.append(float(silhouette_score(X_scaled, labels)))

        # Plot 1: Elbow curve
        plt.figure()
        plt.plot(ks, inertias, marker="o")
        plt.xlabel("Number of Clusters (k)")
        plt.ylabel("Inertia")
        plt.title("Elbow Curve")
        plt.savefig(output_dir / "elbow.png")
        plt.close()

        # Plot 2: Silhouette scores
        plt.figure()
        plt.plot(ks, sil_scores, marker="o")
        plt.xlabel("Number of Clusters (k)")
        plt.ylabel("Silhouette Score")
        plt.title("Silhouette Score vs k")
        plt.savefig(output_dir / "silhouette.png")
        plt.close()

        # Plot 3: PCA scatter colored by best_k labels
        best_k = results["best_k"]
        km_best = KMeans(n_clusters=best_k, random_state=0, n_init=10)
        best_labels = km_best.fit_predict(X_scaled)

        pca = PCA(n_components=2, random_state=0)
        coords = pca.fit_transform(X_scaled)

        plt.figure()
        plt.scatter(coords[:, 0], coords[:, 1], c=best_labels, cmap="tab10", alpha=0.7)
        plt.xlabel("PC1")
        plt.ylabel("PC2")
        plt.title(f"PCA Scatter (k={best_k})")
        plt.colorbar(label="Cluster")
        plt.savefig(output_dir / "pca_scatter.png")
        plt.close()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
