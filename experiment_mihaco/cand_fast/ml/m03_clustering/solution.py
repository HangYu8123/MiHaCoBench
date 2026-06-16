import numpy as np
from sklearn.cluster import KMeans


def fit_predict(X: np.ndarray, n_clusters: int) -> np.ndarray:
    """
    Cluster samples in X into n_clusters groups using K-Means.

    Parameters
    ----------
    X : np.ndarray of shape (n_samples, n_features)
        Input data to cluster.
    n_clusters : int
        Number of clusters.

    Returns
    -------
    np.ndarray of shape (n_samples,)
        Integer cluster labels in [0, n_clusters - 1].
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    return labels.astype(int)
