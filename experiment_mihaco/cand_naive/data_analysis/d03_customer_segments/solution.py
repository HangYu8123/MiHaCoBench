"""
KMeans Customer Segmentation — solution.py
"""

import argparse
import json
import os
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
    """Perform KMeans customer segmentation on the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns: recency, frequency, monetary

    Returns
    -------
    dict with keys: best_k, silhouette, inertia_by_k, cluster_sizes
    """
    # Step 1: Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[["recency", "frequency", "monetary"]])

    # Step 2 & 3: Run KMeans and compute silhouette scores for k in {2,3,4,5,6}
    k_values = [2, 3, 4, 5, 6]
    inertia_by_k = {}
    silhouette_scores = {}

    for k in k_values:
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia_by_k[str(k)] = float(km.inertia_)
        silhouette_scores[k] = float(silhouette_score(X_scaled, labels))

    # Step 4: Choose best_k as k with highest silhouette score
    best_k = max(silhouette_scores, key=silhouette_scores.get)
    best_silhouette = silhouette_scores[best_k]

    # Step 5: Refit KMeans with best_k
    km_final = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    final_labels = km_final.fit_predict(X_scaled)

    # Compute cluster sizes sorted descending
    unique, counts = np.unique(final_labels, return_counts=True)
    cluster_sizes = sorted(counts.tolist(), reverse=True)

    return {
        "best_k": int(best_k),
        "silhouette": best_silhouette,
        "inertia_by_k": inertia_by_k,
        "cluster_sizes": cluster_sizes,
    }


def main(argv=None) -> int:
    """CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(description="KMeans Customer Segmentation")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        # Read CSV
        df = pd.read_csv(args.data)

        # Run analysis
        results = analyze(df)

        # Create output directory if needed
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write results.json
        with open(output_dir / "results.json", "w") as f:
            json.dump(results, f)

        # --- Generate plots ---
        # Prepare scaled data and labels for plots
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[["recency", "frequency", "monetary"]])

        k_values = [2, 3, 4, 5, 6]
        inertias = []
        sil_scores = []

        for k in k_values:
            km = KMeans(n_clusters=k, random_state=0, n_init=10)
            labels = km.fit_predict(X_scaled)
            inertias.append(km.inertia_)
            sil_scores.append(silhouette_score(X_scaled, labels))

        # 1. Elbow curve: inertia vs k
        fig, ax = plt.subplots()
        ax.plot(k_values, inertias, marker="o")
        ax.set_xlabel("k")
        ax.set_ylabel("Inertia")
        ax.set_title("Elbow Curve: Inertia vs k")
        fig.savefig(output_dir / "elbow_curve.png")
        plt.close(fig)

        # 2. Silhouette score vs k
        fig, ax = plt.subplots()
        ax.plot(k_values, sil_scores, marker="o", color="orange")
        ax.set_xlabel("k")
        ax.set_ylabel("Silhouette Score")
        ax.set_title("Silhouette Score vs k")
        fig.savefig(output_dir / "silhouette_scores.png")
        plt.close(fig)

        # 3. 2D PCA scatter plot colored by cluster assignment
        best_k = results["best_k"]
        km_final = KMeans(n_clusters=best_k, random_state=0, n_init=10)
        final_labels = km_final.fit_predict(X_scaled)

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        fig, ax = plt.subplots()
        scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=final_labels, cmap="tab10", s=20)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title(f"PCA Scatter Plot — k={best_k} clusters")
        plt.colorbar(scatter, ax=ax, label="Cluster")
        fig.savefig(output_dir / "pca_scatter.png")
        plt.close(fig)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
