import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """
    Reduce dimensionality of X using PCA, retaining at least `variance`
    cumulative explained variance ratio.

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, 64)
        Raw digit features as returned by load_digits().
    variance : float in (0, 1], default 0.95
        Minimum cumulative explained variance ratio to capture.

    Returns
    -------
    X_reduced : np.ndarray of shape (n_samples, n_components)
        X projected onto the principal components.
    n_components : int
        Minimum number of PCA components whose cumulative explained
        variance ratio is >= variance.
    """
    # Fit PCA with all components to get full variance information
    n_features = X.shape[1]
    pca_full = PCA(n_components=n_features, random_state=0)
    pca_full.fit(X)

    # Find minimum number of components to reach desired variance
    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    # Find first index where cumulative variance >= requested variance
    indices = np.where(cumulative_variance >= variance)[0]
    if len(indices) == 0:
        # If we can't reach desired variance with all components, use all
        n_components = n_features
    else:
        n_components = int(indices[0]) + 1  # +1 because 0-indexed

    # Fit PCA with exactly n_components for efficiency and project X
    pca = PCA(n_components=n_components, random_state=0)
    X_reduced = pca.fit_transform(X)

    return X_reduced, n_components
