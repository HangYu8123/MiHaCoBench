"""Gold reference for ml/m02_regression — diabetes disease progression regression.

Public contract:
    train(X, y) -> model
    predict(model, X) -> numpy.ndarray of shape (n_samples,)
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def train(X: np.ndarray, y: np.ndarray) -> object:
    """Fit a Ridge regression pipeline on the training data.

    Parameters
    ----------
    X : array of shape (n_samples, n_features)
        Feature matrix.
    y : array of shape (n_samples,)
        Continuous target values.

    Returns
    -------
    model : fitted sklearn Pipeline
    """
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=1.0)),
    ])
    pipeline.fit(X, y)
    return pipeline


def predict(model: object, X: np.ndarray) -> np.ndarray:
    """Return continuous predictions for X using the trained model.

    Parameters
    ----------
    model : the object returned by ``train``.
    X     : array of shape (n_samples, n_features)

    Returns
    -------
    predictions : numpy.ndarray of shape (n_samples,), dtype float64
    """
    return np.asarray(model.predict(X), dtype=np.float64)
