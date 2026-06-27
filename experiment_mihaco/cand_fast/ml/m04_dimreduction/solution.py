import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """
    Reduce dimensionality of X using PCA, retaining at least `variance`
    fraction of cumulative explained variance.

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, n_features)
        Raw input features.
    variance : float in (0, 1], default 0.95
        Minimum cumulative explained variance ratio to retain.

    Returns
    -------
    X_reduced : np.ndarray of shape (n_samples, n_components)
        X projected onto the first n_components principal components.
    n_components : int
        The minimum number of PCA components whose cumulative explained
        variance ratio >= variance.
    """
    pca = PCA(n_components=None, svd_solver='full', random_state=0)
    X_transformed = pca.fit_transform(X)

    cumsum = np.cumsum(pca.explained_variance_ratio_)

    # Find minimum k such that cumsum[k-1] >= variance.
    # np.argmax returns first True index (0-based); +1 converts to count.
    # Edge case: variance=1.0 — float precision may mean cumsum never reaches
    # exactly 1.0, making mask all-False and argmax returning 0 incorrectly.
    # The `else len(cumsum)` branch handles this by returning all components.
    mask = cumsum >= variance
    k = int(np.argmax(mask)) + 1 if mask.any() else len(cumsum)

    X_reduced = X_transformed[:, :k]
    return (X_reduced, int(k))
