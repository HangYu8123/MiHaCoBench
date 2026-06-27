import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """
    Reduce dimensionality of X using PCA, retaining enough components to
    explain at least `variance` fraction of total variance.

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, 64)
        Raw digit features from load_digits().
    variance : float in (0, 1]
        Minimum cumulative explained variance ratio to capture (default 0.95).

    Returns
    -------
    X_reduced : np.ndarray of shape (n_samples, n_components)
        X projected onto the selected principal components.
    n_components : int
        Minimum number of PCA components whose cumulative explained variance
        ratio is >= variance.
    """
    # svd_solver='full' forces LAPACK exact SVD — fully deterministic,
    # no random_state needed. n_components=None keeps all components so
    # cumsum[-1] == 1.0 exactly, handling variance=1.0 correctly.
    pca = PCA(n_components=None, svd_solver='full')
    X_transformed = pca.fit_transform(X)

    cumsum = np.cumsum(pca.explained_variance_ratio_)

    # np.searchsorted returns the leftmost index where cumsum >= variance.
    # Adding 1 converts 0-based index to component count.
    # This is safe for variance=1.0: full SVD guarantees cumsum[-1] == 1.0.
    k = int(np.searchsorted(cumsum, variance, side='left') + 1)

    # Clip to valid range in case of floating-point edge cases
    k = min(k, X_transformed.shape[1])

    X_reduced = X_transformed[:, :k]
    return X_reduced, k
