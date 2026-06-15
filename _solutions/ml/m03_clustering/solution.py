"""Gold reference for ml/m03_clustering — K-Means clustering with a known cluster count."""
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans


def fit_predict(X: np.ndarray, n_clusters: int) -> np.ndarray:
    """Cluster X into n_clusters groups and return an integer label array.

    Parameters
    ----------
    X:
        2-D float array of shape (n_samples, n_features).
    n_clusters:
        The true number of clusters in the data (provided by the caller).

    Returns
    -------
    labels:
        1-D integer array of shape (n_samples,) with cluster ids in
        [0, n_clusters - 1].  Label permutation is arbitrary — the caller
        uses adjusted_rand_score which is permutation-invariant.
    """
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(X)
    return labels.astype(int)
