"""Binary classification on the sklearn breast cancer dataset.

Public API
----------
train(X, y)        -> fitted model
predict(model, X)  -> numpy.ndarray of int class labels (0 or 1)
"""

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


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
    model : sklearn.pipeline.Pipeline
        A fitted Pipeline (StandardScaler -> LogisticRegression) that
        exposes a `predict(X)` method at the top level.

    Notes
    -----
    * No internal train/test split is performed — the pipeline is fit on
      the entire (X, y) supplied by the caller.
    * `random_state=42` is fixed for reproducibility.
    * `max_iter=10000` prevents ConvergenceWarning with the lbfgs solver
      on this dataset.
    """
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=10000, random_state=42)),
    ])
    pipeline.fit(X, y)
    return pipeline


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

    Notes
    -----
    * Does not import or load the breast cancer dataset.
    * Returns integers (not probabilities) via `.predict()`, not
      `.predict_proba()`.
    * The explicit `astype(int)` cast guards against platform-specific
      dtype variance (e.g., int32 vs int64) in sklearn's LabelEncoder.
    """
    raw = model.predict(X)
    return np.asarray(raw, dtype=int)
