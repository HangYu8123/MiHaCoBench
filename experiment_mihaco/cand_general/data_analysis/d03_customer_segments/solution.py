"""
solution.py — KMeans Customer Segmentation
Data Analysis 03: d03_customer_segments
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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform KMeans customer segmentation on recency/frequency/monetary columns.

    Returns a dict with keys:
      - best_k: int
      - silhouette: float
      - inertia_by_k: {str(k): float} for k in 2..6
      - cluster_sizes: list[int] sorted descending
    """
    # Step 1: Standardize the three features
    features = df[["recency", "frequency", "monetary"]].values
    X = StandardScaler().fit_transform(features)

    # Steps 2-3: Run KMeans and compute silhouette for each k in {2,3,4,5,6}
    inertias = {}
    sil_scores = {}
    models = {}

    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        km.fit(X)
        inertias[str(k)] = float(km.inertia_)
        sil_scores[k] = float(silhouette_score(X, km.labels_))
        models[k] = km

    # Step 4: Choose best_k as the k with highest silhouette score
    best_k = int(max(sil_scores, key=sil_scores.get))

    # Step 5: Refit KMeans with best_k to obtain final cluster labels
    best_km = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    best_km.fit(X)
    labels = best_km.labels_

    # Cluster sizes: count per cluster, sorted descending
    cluster_sizes = sorted(
        [int(x) for x in np.bincount(labels, minlength=best_k)],
        reverse=True
    )
    # Filter out zero counts (safety for non-contiguous labels)
    cluster_sizes = [s for s in cluster_sizes if s > 0]

    return {
        "best_k": best_k,
        "silhouette": float(sil_scores[best_k]),
        "inertia_by_k": inertias,
        "cluster_sizes": cluster_sizes,
    }


def main(argv=None) -> int:
    """
    CLI entry point:
      python solution.py --data <csv_path> --output-dir <dir>
    """
    try:
        parser = argparse.ArgumentParser(
            description="KMeans customer segmentation"
        )
        parser.add_argument("--data", required=True, help="Path to customers CSV")
        parser.add_argument(
            "--output-dir", dest="output_dir", required=True,
            help="Directory to write output files"
        )
        args = parser.parse_args(argv)

        os.makedirs(args.output_dir, exist_ok=True)

        # Read CSV and run analysis
        df = pd.read_csv(args.data)
        result = analyze(df)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result, f)

        # Re-derive X for plotting (keeps analyze self-contained)
        features = df[["recency", "frequency", "monetary"]].values
        X = StandardScaler().fit_transform(features)

        best_k = result["best_k"]
        ks = list(range(2, 7))

        # Recover inertia values from result (already computed)
        inertia_values = [result["inertia_by_k"][str(k)] for k in ks]

        # Recover silhouette values: recompute from stored KMeans (same params → deterministic)
        sil_values = []
        for k in ks:
            km = KMeans(n_clusters=k, random_state=0, n_init=10)
            km.fit(X)
            sil_values.append(float(silhouette_score(X, km.labels_)))

        # Plot 1: Elbow curve (inertia vs k)
        plt.figure()
        plt.plot(ks, inertia_values, marker="o")
        plt.xlabel("Number of clusters (k)")
        plt.ylabel("Inertia")
        plt.title("Elbow Curve")
        plt.savefig(os.path.join(args.output_dir, "elbow.png"))
        plt.close()

        # Plot 2: Silhouette score vs k
        plt.figure()
        plt.plot(ks, sil_values, marker="o")
        plt.xlabel("Number of clusters (k)")
        plt.ylabel("Silhouette Score")
        plt.title("Silhouette Score vs k")
        plt.savefig(os.path.join(args.output_dir, "silhouette.png"))
        plt.close()

        # Plot 3: 2D PCA scatter plot colored by best-k cluster assignment
        pca = PCA(n_components=2, random_state=0)
        coords = pca.fit_transform(X)

        best_km = KMeans(n_clusters=best_k, random_state=0, n_init=10)
        best_km.fit(X)
        labels = best_km.labels_

        plt.figure()
        plt.scatter(coords[:, 0], coords[:, 1], c=labels, cmap="tab10", s=10)
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.title(f"PCA Scatter Plot (k={best_k})")
        plt.colorbar(label="Cluster")
        plt.savefig(os.path.join(args.output_dir, "pca_scatter.png"))
        plt.close()

        return 0

    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
