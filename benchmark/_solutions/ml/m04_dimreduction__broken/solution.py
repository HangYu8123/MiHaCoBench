"""Deliberately-broken reference for ml/m04_dimreduction.

Planted defect: reduce() always returns a fixed n_components=2 regardless of
the variance argument. This causes:
  - wrong n_components for variance >= 0.95 (correct answer is much larger)
  - X_reduced has shape (n_samples, 2) instead of (n_samples, k)
  - downstream LogisticRegression accuracy on 2 components is far below 0.90
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """Return (X_reduced, n_components) — BUG: always uses n_components=2."""
    # BUG: ignore variance and hard-code 2 components
    n_components = 2
    pca = PCA(n_components=n_components, random_state=0)
    X_reduced = pca.fit_transform(X)
    return X_reduced, n_components
