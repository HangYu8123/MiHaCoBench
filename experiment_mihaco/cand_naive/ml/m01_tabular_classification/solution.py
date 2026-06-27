import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def train(X: np.ndarray, y: np.ndarray) -> object:
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
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
        )),
    ])
    model.fit(X, y)
    return model


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
        Predicted integer class labels (0 or 1).
    """
    return model.predict(X)
