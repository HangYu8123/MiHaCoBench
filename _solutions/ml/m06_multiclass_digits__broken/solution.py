"""Deliberately-broken reference for ml/m06_multiclass_digits.

Planted defect: train() returns a DummyClassifier(strategy="most_frequent")
instead of a real model. On the 10-class balanced digits dataset, this always
predicts the same majority class, yielding ~10% accuracy — well below the 0.95
threshold. The anti-leakage test still passes because a constant predictor
trained on shuffled labels also collapses to <0.30.
"""
from __future__ import annotations

import numpy as np
from sklearn.dummy import DummyClassifier


def train(X: np.ndarray, y: np.ndarray) -> object:
    """BUG: fits a majority-class dummy instead of a real classifier.

    This causes held-out accuracy to collapse to ~10% (one class out of 10),
    failing the grader's accuracy > 0.95 threshold.
    """
    # BUG: uses a constant/majority-class dummy classifier, not a real model
    model = DummyClassifier(strategy="most_frequent", random_state=42)
    model.fit(X, y)
    return model


def predict(model: object, X: np.ndarray) -> np.ndarray:
    """Return class-label predictions for X using the fitted model."""
    return model.predict(X)
