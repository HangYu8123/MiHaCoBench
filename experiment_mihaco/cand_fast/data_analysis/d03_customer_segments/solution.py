"""
KMeans Customer Segmentation — solution.py
"""
from __future__ import annotations

import argparse
import json
import os

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
    """Perform KMeans customer segmentation on the RFM DataFrame."""
    # Step 1: Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[["recency", "frequency", "monetary"]])

    # Step 2 & 3: Loop over k values, compute inertia and silhouette
    inertia_by_k: dict[str, float] = {}
    silhouettes: dict[int, float] = {}

    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia_by_k[str(k)] = float(km.inertia_)
        silhouettes[k] = float(silhouette_score(X_scaled, labels))

    # Step 4: Choose best_k as k with highest silhouette score
    best_k = int(max(silhouettes, key=silhouettes.__getitem__))
    best_silhouette = float(silhouettes[best_k])

    # Step 5: Refit KMeans with best_k for canonical final labels
    km_final = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    final_labels = km_final.fit_predict(X_scaled)

    # cluster_sizes sorted descending — native Python ints via .tolist()
    cluster_sizes = sorted(np.bincount(final_labels).tolist(), reverse=True)

    return {
        "best_k": best_k,
        "silhouette": best_silhouette,
        "inertia_by_k": inertia_by_k,
        "cluster_sizes": cluster_sizes,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    try:
        parser = argparse.ArgumentParser(description="KMeans Customer Segmentation")
        parser.add_argument("--data", required=True, help="Path to customers CSV")
        parser.add_argument("--output-dir", required=True, help="Directory for outputs")
        args = parser.parse_args(argv)

        df = pd.read_csv(args.data)
        result = analyze(df)

        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Write results.json
        with open(os.path.join(output_dir, "results.json"), "w") as f:
            json.dump(result, f)

        # --- Prepare scaled data and PCA for plots ---
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[["recency", "frequency", "monetary"]])

        k_values = list(range(2, 7))
        inertias = [result["inertia_by_k"][str(k)] for k in k_values]

        # Recompute silhouette scores for plotting
        sil_scores = []
        for k in k_values:
            km = KMeans(n_clusters=k, random_state=0, n_init=10)
            labels = km.fit_predict(X_scaled)
            sil_scores.append(float(silhouette_score(X_scaled, labels)))

        # Refit final model for PCA scatter
        best_k = result["best_k"]
        km_final = KMeans(n_clusters=best_k, random_state=0, n_init=10)
        final_labels = km_final.fit_predict(X_scaled)

        # PCA for scatter
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        # Plot 1: Elbow curve
        fig, ax = plt.subplots()
        ax.plot(k_values, inertias, marker="o")
        ax.set_xlabel("k")
        ax.set_ylabel("Inertia")
        ax.set_title("Elbow Curve: Inertia vs k")
        fig.savefig(os.path.join(output_dir, "elbow.png"))
        plt.close(fig)

        # Plot 2: Silhouette score vs k
        fig, ax = plt.subplots()
        ax.plot(k_values, sil_scores, marker="o")
        ax.set_xlabel("k")
        ax.set_ylabel("Silhouette Score")
        ax.set_title("Silhouette Score vs k")
        fig.savefig(os.path.join(output_dir, "silhouette.png"))
        plt.close(fig)

        # Plot 3: PCA scatter colored by cluster labels
        fig, ax = plt.subplots()
        scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=final_labels, cmap="tab10")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title(f"PCA Scatter — k={best_k} clusters")
        fig.colorbar(scatter, ax=ax, label="Cluster")
        fig.savefig(os.path.join(output_dir, "pca_scatter.png"))
        plt.close(fig)

        return 0

    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
