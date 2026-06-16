import numpy as np
from sklearn.cluster import KMeans


def fit_predict(X: np.ndarray, n_clusters: int) -> np.ndarray:
    """
    Cluster samples in X into n_clusters groups using K-Means.

    Parameters
    ----------
    X : np.ndarray, shape (n_samples, n_features)
        2-D float array of input data.
    n_clusters : int
        Number of clusters (provided by the grader).

    Returns
    -------
    np.ndarray, shape (n_samples,)
        Integer cluster labels in range [0, n_clusters - 1].
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    return labels.astype(int)
