import numpy as np
from sklearn.decomposition import PCA


def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    """
    Reduce dimensionality of X using PCA to capture at least `variance`
    cumulative explained variance ratio.

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, 64)
        Raw digit features from load_digits().
    variance : float in (0, 1], default 0.95
        Minimum cumulative explained variance ratio to capture.

    Returns
    -------
    X_reduced : np.ndarray of shape (n_samples, n_components)
        X projected onto the selected principal components.
    n_components : int
        Minimum number of PCA components whose cumulative explained variance
        ratio is >= variance.
    """
    # Fit PCA on all features (up to min(n_samples, n_features) components)
    pca = PCA(random_state=0)
    pca.fit(X)

    # Compute cumulative explained variance ratio
    cumsum = np.cumsum(pca.explained_variance_ratio_)

    # Find the minimum number of components to reach the target variance
    # np.argmax returns the first index where condition is True (0-based)
    # Add 1 to convert to component count
    n_components = int(np.argmax(cumsum >= variance) + 1)

    # Clamp to valid range (handles edge cases like variance=1.0)
    n_components = min(n_components, X.shape[1])

    # Project X onto the selected components
    X_transformed = pca.transform(X)
    X_reduced = X_transformed[:, :n_components]

    return X_reduced, n_components
