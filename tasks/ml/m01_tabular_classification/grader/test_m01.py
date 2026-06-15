"""Grader for ml/m01_tabular_classification. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Tests
-----
1. test_train_returns_model_with_predict   — model has .predict method
2. test_predict_shape                      — output shape matches test set
3. test_predict_dtype_labels              — output contains only 0/1 labels
4. test_held_out_accuracy_above_threshold — accuracy > 0.92 on grader's own split
5. test_anti_leakage_mislabelled          — shuffled labels collapse accuracy < 0.75
6. test_predict_is_numpy_array            — output is a numpy ndarray
7. test_model_reuse                        — same model predicts consistently
8. test_code_quality (advisory)           — code_quality_report, never asserted
"""
import numpy as np
import pytest
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "ml", "m01_tabular_classification"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

train_fn = gu.load_callable(SOL, "solution.py", "train")
predict_fn = gu.load_callable(SOL, "solution.py", "predict")

# --- Fixed split (grader owns this; solution must NOT hard-code it) -----------
_data = load_breast_cancer()
X_ALL, y_ALL = _data.data, _data.target

X_TRAIN, X_TEST, y_TRAIN, y_TEST = train_test_split(
    X_ALL, y_ALL, test_size=0.25, random_state=0, stratify=y_ALL
)

# Fit once and cache so most tests share the same model object.
_MODEL = train_fn(X_TRAIN, y_TRAIN)
_PRED = predict_fn(_MODEL, X_TEST)


# ---------------------------------------------------------------------------
# Test 1 — the returned object must expose .predict
# ---------------------------------------------------------------------------
def test_train_returns_model_with_predict():
    """train() must return an object with a .predict method."""
    assert hasattr(_MODEL, "predict"), (
        "train() must return an estimator with a .predict method"
    )
    assert callable(_MODEL.predict)


# ---------------------------------------------------------------------------
# Test 2 — prediction array shape
# ---------------------------------------------------------------------------
def test_predict_shape():
    """predict() output length must match number of test samples."""
    assert len(_PRED) == len(X_TEST), (
        f"expected {len(X_TEST)} predictions, got {len(_PRED)}"
    )


# ---------------------------------------------------------------------------
# Test 3 — predictions contain only valid class labels (0 or 1)
# ---------------------------------------------------------------------------
def test_predict_dtype_labels():
    """predict() must return only 0 and 1 as labels."""
    unique = set(np.unique(_PRED).tolist())
    assert unique.issubset({0, 1}), (
        f"predict() returned unexpected labels: {unique}"
    )


# ---------------------------------------------------------------------------
# Test 4 — held-out accuracy must exceed the documented threshold
# ---------------------------------------------------------------------------
def test_held_out_accuracy_above_threshold():
    """Held-out accuracy on the grader's own split must exceed 0.92."""
    acc = accuracy_score(y_TEST, _PRED)
    assert acc > 0.92, (
        f"held-out accuracy {acc:.4f} did not exceed the required threshold 0.92"
    )


# ---------------------------------------------------------------------------
# Test 5 — anti-leakage: mislabelled training data must collapse accuracy
# ---------------------------------------------------------------------------
def test_anti_leakage_mislabelled():
    """Train on shuffled (mislabelled) labels — held-out accuracy must collapse
    toward chance (< 0.75), proving the model actually learns from training labels.
    """
    rng = np.random.default_rng(seed=7)
    # Randomly permute the training labels with a fixed seed.
    y_shuffled = rng.permutation(y_TRAIN)
    model_bad = train_fn(X_TRAIN, y_shuffled)
    pred_bad = predict_fn(model_bad, X_TEST)
    acc_bad = accuracy_score(y_TEST, pred_bad)
    assert acc_bad < 0.75, (
        f"Expected accuracy to collapse toward chance on mislabelled data, "
        f"but got {acc_bad:.4f} >= 0.75 — possible data leakage."
    )


# ---------------------------------------------------------------------------
# Test 6 — output must be a numpy ndarray
# ---------------------------------------------------------------------------
def test_predict_is_numpy_array():
    """predict() must return a numpy ndarray, not a list or other type."""
    assert isinstance(_PRED, np.ndarray), (
        f"predict() returned {type(_PRED).__name__}, expected numpy.ndarray"
    )


# ---------------------------------------------------------------------------
# Test 7 — model reuse: calling predict twice gives the same result
# ---------------------------------------------------------------------------
def test_model_reuse():
    """The same fitted model must produce identical predictions on repeated calls."""
    pred2 = predict_fn(_MODEL, X_TEST)
    assert np.array_equal(_PRED, pred2), (
        "predict() returned different results on two calls with the same model and data"
    )


# ---------------------------------------------------------------------------
# Test 8 (advisory) — code quality report
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory code quality report — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
