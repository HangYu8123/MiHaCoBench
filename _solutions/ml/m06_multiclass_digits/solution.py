"""Gold reference for ml/m06_multiclass_digits.

Fits a StandardScaler + SVC(rbf) pipeline on the digits dataset
(scikit-learn bundled). Consistently achieves >0.97 held-out accuracy
with the grader's split (test_size=0.25, random_state=0, stratify=y).
"""
from __future__ import annotations

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


def train(X: np.ndarray, y: np.ndarray) -> object:
    """Fit a SVM pipeline and return the fitted estimator.

    Parameters
    ----------
    X : numpy.ndarray of shape (n_samples, n_features)
        Training feature matrix (pixel values, n_features=64).
    y : numpy.ndarray of shape (n_samples,)
        Integer class labels in {0, 1, ..., 9}.

    Returns
    -------
    model : Pipeline
        A fitted scikit-learn Pipeline with .predict method.
    """
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SVC(kernel="rbf", C=10.0, gamma="scale", random_state=42)),
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
        Predicted integer class labels in {0, 1, ..., 9}.
    """
    return model.predict(X)
