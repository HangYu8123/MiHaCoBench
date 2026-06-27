import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """Reduce dimensionality of X using PCA, retaining at least `variance` of explained variance.

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, 64)
        Raw digit features from load_digits().
    variance : float in (0, 1], default=0.95
        Minimum cumulative explained variance ratio to capture.

    Returns
    -------
    X_reduced : np.ndarray of shape (n_samples, n_components)
        X projected onto the principal components.
    n_components : int
        Minimum number of PCA components needed to achieve >= variance cumulative explained variance.
    """
    # Fit PCA with all components to get the full explained variance ratios
    pca_full = PCA(n_components=None, random_state=0)
    pca_full.fit(X)

    # Find the minimum number of components to reach >= variance cumulative explained variance
    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    # n_components is the index (1-based) where cumulative variance first meets the threshold
    n_components = int(np.searchsorted(cumulative_variance, variance) + 1)

    # Fit PCA with exactly n_components and transform X
    pca = PCA(n_components=n_components, random_state=0)
    X_reduced = pca.fit_transform(X)

    return X_reduced, n_components
