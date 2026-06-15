"""Gold reference for ml/m01_tabular_classification.

Fits a logistic-regression classifier on the breast cancer dataset
(scikit-learn bundled). Consistently achieves >0.97 held-out accuracy
with the grader's split (test_size=0.25, random_state=0, stratify=y).
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def train(X: np.ndarray, y: np.ndarray) -> object:
    """Fit a logistic-regression pipeline and return the fitted estimator.

    Parameters
    ----------
    X : numpy.ndarray of shape (n_samples, n_features)
        Training feature matrix.
    y : numpy.ndarray of shape (n_samples,)
        Integer class labels (0 or 1).

    Returns
    -------
    model : Pipeline
        A fitted scikit-learn Pipeline with .predict method.
    """
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    model.fit(X, y)
    return model


def predict(model: object, X: np.ndarray) -> np.ndarray:
    """Return class-label predictions for X using the fitted model.

    Parameters
    ----------
    model : object
        A fitted estimator as returned by train().
    X : numpy.ndarray of shape (n_samples, n_features)
        Feature matrix.

    Returns
    -------
    predictions : numpy.ndarray of shape (n_samples,)
        Predicted integer class labels (0 or 1).
    """
    return model.predict(X)
