"""Deliberately-broken reference for ml/m02_regression.

Planted defect: predict always returns the mean of the training labels
(stored during train), ignoring X entirely. This yields R² ≈ 0 on the
held-out set and must fail the grader's > 0.40 threshold test.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def train(X: np.ndarray, y: np.ndarray) -> object:
    """Fit a model but also memorise the training mean (used in broken predict)."""
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=1.0)),
    ])
    pipeline.fit(X, y)
    # Store training mean on the pipeline object so predict can use it
    pipeline._train_mean = float(np.mean(y))  # type: ignore[attr-defined]
    return pipeline


def predict(model: object, X: np.ndarray) -> np.ndarray:
    """BUG: ignores X and returns a constant array equal to the training mean.

    This achieves R² ≈ 0 (or negative) and must fail the ≥ 0.40 threshold.
    """
    n = X.shape[0]
    # Always return training mean regardless of input — deliberate defect
    mean_val = getattr(model, "_train_mean", 0.0)
    return np.full(n, mean_val, dtype=np.float64)
