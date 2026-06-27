"""
solution.py — KMeans Customer Segmentation
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
    Perform KMeans customer segmentation.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain columns 'recency', 'frequency', 'monetary'.

    Returns
    -------
    dict with keys: best_k, silhouette, inertia_by_k, cluster_sizes
    """
    features = df[["recency", "frequency", "monetary"]].values

    # Step 1: Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # Step 2 & 3: Run KMeans for each k and compute silhouette scores
    ks = [2, 3, 4, 5, 6]
    inertia_by_k = {}
    silhouette_scores = {}

    for k in ks:
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia_by_k[str(k)] = float(km.inertia_)
        silhouette_scores[k] = float(silhouette_score(X_scaled, labels))

    # Step 4: Choose best_k
    best_k = max(silhouette_scores, key=lambda k: silhouette_scores[k])
    best_silhouette = silhouette_scores[best_k]

    # Step 5: Refit KMeans with best_k
    best_km = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    best_labels = best_km.fit_predict(X_scaled)

    # Compute cluster sizes sorted descending
    unique, counts = np.unique(best_labels, return_counts=True)
    cluster_sizes = sorted(counts.tolist(), reverse=True)

    return {
        "best_k": int(best_k),
        "silhouette": best_silhouette,
        "inertia_by_k": inertia_by_k,
        "cluster_sizes": cluster_sizes,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="KMeans Customer Segmentation")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.data)
        result = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        # Write results.json
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result, f)

        # Prepare scaled data and cluster labels for plots
        features = df[["recency", "frequency", "monetary"]].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        ks = [2, 3, 4, 5, 6]
        inertias = [result["inertia_by_k"][str(k)] for k in ks]

        # Re-compute silhouette scores for plotting
        sil_scores = []
        for k in ks:
            km = KMeans(n_clusters=k, random_state=0, n_init=10)
            labels = km.fit_predict(X_scaled)
            sil_scores.append(float(silhouette_score(X_scaled, labels)))

        # Plot 1: Elbow curve (inertia vs k)
        fig, ax = plt.subplots()
        ax.plot(ks, inertias, marker="o")
        ax.set_xlabel("k")
        ax.set_ylabel("Inertia")
        ax.set_title("Elbow Curve")
        elbow_path = os.path.join(args.output_dir, "elbow_curve.png")
        fig.savefig(elbow_path)
        plt.close(fig)

        # Plot 2: Silhouette score vs k
        fig, ax = plt.subplots()
        ax.plot(ks, sil_scores, marker="o", color="orange")
        ax.set_xlabel("k")
        ax.set_ylabel("Silhouette Score")
        ax.set_title("Silhouette Score vs k")
        sil_path = os.path.join(args.output_dir, "silhouette_scores.png")
        fig.savefig(sil_path)
        plt.close(fig)

        # Plot 3: 2D PCA scatter plot colored by cluster assignment
        best_k = result["best_k"]
        best_km = KMeans(n_clusters=best_k, random_state=0, n_init=10)
        best_labels = best_km.fit_predict(X_scaled)

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        fig, ax = plt.subplots()
        scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=best_labels, cmap="tab10", alpha=0.7)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title(f"PCA Scatter Plot (k={best_k})")
        fig.colorbar(scatter, ax=ax, label="Cluster")
        pca_path = os.path.join(args.output_dir, "pca_scatter.png")
        fig.savefig(pca_path)
        plt.close(fig)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
