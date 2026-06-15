"""Deliberately-broken reference for ml/m01_tabular_classification.

Planted defect: predict() ignores the fitted model entirely and always
returns the majority-class label (all zeros). This causes held-out accuracy
to collapse well below 0.92, failing the grader's accuracy threshold test.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def train(X: np.ndarray, y: np.ndarray) -> object:
    """Fit a logistic-regression pipeline and return the fitted estimator."""
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    model.fit(X, y)
    return model


def predict(model: object, X: np.ndarray) -> np.ndarray:
    """BUG: ignores model; always predicts the majority class (0 = malignant).

    This causes held-out accuracy to collapse to ~37% on the breast cancer
    dataset (since class 1 / benign is the majority at ~63%, returning all
    zeros gives ~37% accuracy — well below the 0.92 threshold).
    """
    # BUG: completely ignores `model` and returns all zeros
    return np.zeros(len(X), dtype=int)
