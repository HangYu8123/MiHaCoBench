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
    np.ndarray, shape (n_samples,)
        Integer cluster labels in [0, n_clusters - 1].
    """
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    return kmeans.fit_predict(X)
