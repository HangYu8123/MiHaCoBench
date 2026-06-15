"""Deliberately-broken reference for ml/m03_clustering.

Planted defect: assigns ALL samples to cluster 0 regardless of the data.
This yields an adjusted_rand_score of approximately 0 (catastrophically wrong
clustering), which will fail the ARI threshold tests.
"""
from __future__ import annotations

import numpy as np


def fit_predict(X: np.ndarray, n_clusters: int) -> np.ndarray:
    """Broken clustering: always assigns every point to cluster 0."""
    # BUG: ignores X and n_clusters entirely; all labels are 0
    return np.zeros(len(X), dtype=int)
