import numpy as np
from sklearn.cluster import KMeans


def fit_predict(X: np.ndarray, n_clusters: int) -> np.ndarray:
    """Cluster X into n_clusters groups using K-Means.

    Parameters
    ----------
    X : np.ndarray, shape (n_samples, n_features)
        Input data.
    n_clusters : int
        Number of clusters (provided by the grader).

    Returns
    -------
    np.ndarray, shape (n_samples,), dtype int
        Cluster label for each sample, values in [0, n_clusters - 1].
    """
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(X)
    return labels.astype(int)
