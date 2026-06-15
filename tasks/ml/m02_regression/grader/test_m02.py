"""Grader for ml/m02_regression. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken variant returns a constant (training mean) for every prediction,
which yields R² ≈ 0 and must fail test_r2_above_threshold.
"""
from __future__ import annotations

import numpy as np
import pytest
from sklearn.datasets import load_diabetes
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "ml", "m02_regression"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

train_fn = gu.load_callable(SOL, "solution.py", "train")
predict_fn = gu.load_callable(SOL, "solution.py", "predict")

# ── Fixed dataset split (grader-owned; candidate must not hard-code indices) ──
_X_full, _y_full = load_diabetes(return_X_y=True)
_X_train, _X_test, _y_train, _y_test = train_test_split(
    _X_full, _y_full, test_size=0.25, random_state=0
)

# Fit once; reuse across tests (speeds up the suite)
np.random.seed(0)
_model = train_fn(_X_train.copy(), _y_train.copy())


# ── Test 1: train returns a non-None model object ────────────────────────────
def test_train_returns_model():
    assert _model is not None, "train() must return a model object"


# ── Test 2: predict returns a 1-D array ──────────────────────────────────────
def test_predict_returns_1d_array():
    preds = predict_fn(_model, _X_test)
    assert isinstance(preds, np.ndarray), "predict() must return a numpy.ndarray"
    assert preds.ndim == 1, f"predictions must be 1-D, got shape {preds.shape}"


# ── Test 3: output length matches input rows ──────────────────────────────────
def test_predict_length_matches_input():
    preds = predict_fn(_model, _X_test)
    assert len(preds) == len(_X_test), (
        f"expected {len(_X_test)} predictions, got {len(preds)}"
    )


# ── Test 4: held-out R² exceeds 0.30 (main quality gate) ────────────────────
def test_r2_above_threshold():
    preds = predict_fn(_model, _X_test)
    r2 = r2_score(_y_test, preds)
    assert r2 > 0.30, (
        f"held-out R² = {r2:.4f}; expected > 0.30. "
        "A real regression model on the diabetes dataset should clear this."
    )


# ── Test 5: predictions are finite floats ────────────────────────────────────
def test_predictions_are_finite():
    preds = predict_fn(_model, _X_test)
    assert np.all(np.isfinite(preds)), "all predictions must be finite floats"


# ── Test 6: anti-leakage — shuffled labels collapse R² ───────────────────────
def test_anti_leakage_shuffled_labels():
    """A model trained on shuffled y must score near chance on held-out data.

    This catches solutions that memorise / encode the test set.
    If r2 > 0.05 on a genuinely random label assignment, something is wrong.
    """
    rng = np.random.RandomState(42)
    y_shuffled = rng.permutation(_y_train)
    np.random.seed(0)
    model_shuffled = train_fn(_X_train.copy(), y_shuffled)
    preds_shuffled = predict_fn(model_shuffled, _X_test)
    r2_shuffled = r2_score(_y_test, preds_shuffled)
    assert r2_shuffled < 0.05, (
        f"R² on shuffled-label model = {r2_shuffled:.4f}; expected < 0.05. "
        "The model appears to leak or encode information beyond the training labels."
    )


# ── Test 7: predict works on a small synthetic subset ────────────────────────
def test_predict_small_subset():
    """Predict on just 5 samples; result must have the right shape and be finite."""
    small_X = _X_test[:5]
    preds = predict_fn(_model, small_X)
    assert preds.shape == (5,), f"expected shape (5,), got {preds.shape}"
    assert np.all(np.isfinite(preds))


# ── Test 8: predictions vary across different inputs ─────────────────────────
def test_predictions_not_constant():
    """A constant-output model (e.g. DummyRegressor) must be rejected."""
    preds = predict_fn(_model, _X_test)
    assert np.std(preds) > 1.0, (
        f"predictions have std={np.std(preds):.4f}; "
        "they appear constant — a real regression model should vary."
    )


# ── Advisory: code quality report (never asserted) ───────────────────────────
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
