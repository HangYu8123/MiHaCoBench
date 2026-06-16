"""
Customer Segmentation using KMeans Clustering.

Public contract:
    analyze(df) -> dict
    main(argv=None) -> int
"""

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def analyze(df: pd.DataFrame) -> dict:
    """
    Perform KMeans customer segmentation on the given DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'recency', 'frequency', 'monetary'.

    Returns
    -------
    dict with keys:
        best_k (int): k with the highest silhouette score
        silhouette (float): Silhouette score for best_k
        inertia_by_k ({str: float}): KMeans inertia for k in 2..6
        cluster_sizes (list[int]): Cluster membership counts for best_k, descending
    """
    # Step 1: Standardize the three features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[['recency', 'frequency', 'monetary']])

    # Steps 2 & 3: Run KMeans for each k and compute silhouette scores
    inertia_by_k = {}
    sil_scores = {}

    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=0, n_init=10)
        km.fit(X_scaled)
        inertia_by_k[str(k)] = float(km.inertia_)
        labels = km.labels_
        sil_scores[k] = float(silhouette_score(X_scaled, labels))

    # Step 4: Choose best_k with highest silhouette score
    best_k = max(sil_scores, key=sil_scores.get)
    best_silhouette = sil_scores[best_k]

    # Step 5: Refit KMeans with best_k to get final labels
    km_final = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    km_final.fit(X_scaled)
    final_labels = km_final.labels_

    # Compute cluster sizes sorted descending
    cluster_sizes = sorted(np.bincount(final_labels).tolist(), reverse=True)
    cluster_sizes = [int(x) for x in cluster_sizes]

    return {
        'best_k': int(best_k),
        'silhouette': float(best_silhouette),
        'inertia_by_k': inertia_by_k,
        'cluster_sizes': cluster_sizes,
    }


def main(argv: list = None) -> int:
    """
    CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>

    Returns 0 on success, non-zero on error.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description='KMeans Customer Segmentation')
    parser.add_argument('--data', required=True, help='Path to customers CSV file')
    parser.add_argument('--output-dir', required=True, help='Directory to write outputs')
    args = parser.parse_args(argv)

    try:
        # Load data
        df = pd.read_csv(args.data)

        # Create output directory if needed
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Run analysis
        result = analyze(df)

        # Write results.json
        results_path = os.path.join(output_dir, 'results.json')
        with open(results_path, 'w') as f:
            json.dump(result, f)

        # --- Prepare data for plots ---
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[['recency', 'frequency', 'monetary']])

        inertia_by_k = result['inertia_by_k']
        best_k = result['best_k']

        # Recompute silhouette scores for each k (for the silhouette plot)
        ks = list(range(2, 7))
        sil_scores_list = []
        for k in ks:
            km = KMeans(n_clusters=k, random_state=0, n_init=10)
            km.fit(X_scaled)
            labels = km.labels_
            sil_scores_list.append(float(silhouette_score(X_scaled, labels)))

        # Get final labels for PCA scatter
        km_final = KMeans(n_clusters=best_k, random_state=0, n_init=10)
        km_final.fit(X_scaled)
        final_labels = km_final.labels_

        # --- Plot 1: Elbow curve ---
        inertia_values = [inertia_by_k[str(k)] for k in ks]
        plt.figure()
        plt.plot(ks, inertia_values, marker='o')
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Inertia')
        plt.title('Elbow Curve: Inertia vs k')
        plt.xticks(ks)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'elbow_curve.png'))
        plt.close()

        # --- Plot 2: Silhouette scores vs k ---
        plt.figure()
        plt.plot(ks, sil_scores_list, marker='o')
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Silhouette Score')
        plt.title('Silhouette Score vs k')
        plt.xticks(ks)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'silhouette_scores.png'))
        plt.close()

        # --- Plot 3: PCA scatter colored by cluster ---
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        plt.figure()
        scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=final_labels, cmap='viridis', alpha=0.7)
        plt.colorbar(scatter, label='Cluster')
        plt.xlabel('PC1')
        plt.ylabel('PC2')
        plt.title(f'PCA Scatter (k={best_k})')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'pca_scatter.png'))
        plt.close()

        return 0

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
