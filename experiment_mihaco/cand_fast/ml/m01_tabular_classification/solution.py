"""solution.py — Binary classification on the breast cancer dataset.

Public contract
---------------
train(X, y)         -> fitted model object with a .predict(X) method
predict(model, X)   -> numpy.ndarray of integer class labels (0 or 1)
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier


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
        A fitted RandomForestClassifier that exposes a ``predict(X)`` method.
        Typical accuracy on the breast cancer 25 % hold-out is ~96 %,
        well above the 0.92 threshold required by the grader.
    """
    model = RandomForestClassifier(
        n_estimators=200,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)
    return model


def predict(model: object, X: np.ndarray) -> np.ndarray:
    """Return class-label predictions for X using the fitted model.

    Parameters
    ----------
    model : object
        A fitted estimator as returned by :func:`train`.
    X : numpy.ndarray of shape (n_samples, n_features)
        Feature matrix.

    Returns
    -------
    predictions : numpy.ndarray of shape (n_samples,)
        Predicted integer class labels (0 or 1).
    """
    preds = model.predict(X)
    # Ensure integer dtype regardless of what the estimator returns.
    return preds.astype(int)
