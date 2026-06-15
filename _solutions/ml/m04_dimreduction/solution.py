"""Gold reference for ml/m04_dimreduction — PCA dimensionality reduction.

Exposes a single public function:
    reduce(X, variance=0.95) -> (X_reduced, n_components)

where n_components is the minimum number of PCA principal components whose
cumulative explained variance ratio >= variance, and X_reduced is X projected
onto those components.
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """Return (X_reduced, n_components) using PCA on X.

    Parameters
    ----------
    X:
        2-D array of shape (n_samples, n_features).
    variance:
        Minimum cumulative explained variance ratio to capture (0 < variance <= 1).

    Returns
    -------
    X_reduced:
        X projected onto the first n_components principal components.
        Shape: (n_samples, n_components).
    n_components:
        Minimum number of PC directions whose cumulative explained variance
        ratio >= variance.
    """
    # Fit PCA on all components to get the full explained variance curve.
    n_features = X.shape[1]
    pca_full = PCA(n_components=n_features, random_state=0)
    pca_full.fit(X)

    cumvar = np.cumsum(pca_full.explained_variance_ratio_)
    # Find the minimum k such that cumvar[k-1] >= variance.
    indices = np.where(cumvar >= variance)[0]
    n_components = int(indices[0]) + 1  # 1-based count

    # Project X onto the selected components.
    X_reduced = pca_full.transform(X)[:, :n_components]
    return X_reduced, n_components
