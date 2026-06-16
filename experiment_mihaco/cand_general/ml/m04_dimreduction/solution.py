import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """PCA-based dimensionality reducer.

    Parameters
    ----------
    X : np.ndarray, shape (n_samples, 64)
        Raw digit features from load_digits().
    variance : float, default 0.95
        Minimum cumulative explained variance ratio to capture. In (0, 1].

    Returns
    -------
    X_reduced : np.ndarray, shape (n_samples, n_components)
        X projected onto the selected principal components.
    n_components : int
        Minimum number of PCA components whose cumulative explained variance
        ratio is >= variance.
    """
    pca = PCA(n_components=None, random_state=0)
    pca.fit(X)

    cumsum = np.cumsum(pca.explained_variance_ratio_)

    # Find the first index where cumulative variance >= requested variance.
    # np.searchsorted with side='left' returns the first index where
    # cumsum[idx] >= variance (0-based); +1 converts index to count.
    n_components = int(np.searchsorted(cumsum, variance, side='left')) + 1

    # Guard against floating-point edge case where variance=1.0 but cumsum
    # tops out slightly below 1.0, causing searchsorted to return past-end.
    n_components = min(n_components, len(cumsum))

    X_reduced = pca.transform(X)[:, :n_components]

    return (X_reduced, n_components)
