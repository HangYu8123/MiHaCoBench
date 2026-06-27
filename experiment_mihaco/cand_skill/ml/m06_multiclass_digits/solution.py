import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


def train(X: np.ndarray, y: np.ndarray) -> object:
    """Fit a multiclass classifier on the provided training data and return it.

    Parameters
    ----------
    X : numpy.ndarray of shape (n_samples, n_features)
        Feature matrix (pixel values, n_features=64).
    y : numpy.ndarray of shape (n_samples,)
        Integer class labels in {0, 1, ..., 9}.

    Returns
    -------
    model : object
        A fitted estimator that exposes a `predict(X)` method.
    """
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SVC(kernel="rbf", random_state=42)),
    ])
    pipe.fit(X, y)
    return pipe


def predict(model: object, X: np.ndarray) -> np.ndarray:
    """Return class-label predictions for X using the fitted model.

    Parameters
    ----------
    model : object
        A fitted estimator as returned by `train`.
    X : numpy.ndarray of shape (n_samples, n_features)
        Feature matrix.

    Returns
    -------
    predictions : numpy.ndarray of shape (n_samples,)
        Predicted integer class labels in {0, 1, ..., 9}.
    """
    return model.predict(X)
