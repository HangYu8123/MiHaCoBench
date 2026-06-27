import numpy
from sklearn.ensemble import RandomForestClassifier


def train(X: numpy.ndarray, y: numpy.ndarray) -> object:
    """Fit a classifier on the provided training data and return it.

    Parameters
    ----------
    X : numpy.ndarray of shape (n_samples, n_features)
        Feature matrix.
    y : numpy.ndarray of shape (n_samples,)
        Integer class labels (0 or 1).

    Returns
    -------
    model : object
        A fitted estimator that exposes a `predict(X)` method.
    """
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)
    return model


def predict(model: object, X: numpy.ndarray) -> numpy.ndarray:
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
        Predicted integer class labels (0 or 1).
    """
    return model.predict(X)
