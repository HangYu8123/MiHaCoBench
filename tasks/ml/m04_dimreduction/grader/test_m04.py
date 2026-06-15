"""Grader for ml/m04_dimreduction. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken variant always returns n_components=2 regardless of the variance
argument, so it fails the n_components check and the downstream accuracy test.
"""
from __future__ import annotations

import numpy as np
import pytest
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "ml", "m04_dimreduction"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

reduce_fn = gu.load_callable(SOL, "solution.py", "reduce")

# ── Fixed dataset (grader-owned; never re-randomise) ───────────────────────
_X_full, _y_full = load_digits(return_X_y=True)   # shape (1797, 64)

# ── Reference: compute true minimum n_components for variance=0.95 ─────────
_pca_ref = PCA(n_components=_X_full.shape[1], random_state=0)
_pca_ref.fit(_X_full)
_cumvar_ref = np.cumsum(_pca_ref.explained_variance_ratio_)
_TRUE_K_95 = int(np.where(_cumvar_ref >= 0.95)[0][0]) + 1  # should be 29


# ── Test 1: reduce returns a 2-tuple ───────────────────────────────────────
def test_reduce_returns_tuple():
    result = reduce_fn(_X_full, 0.95)
    assert isinstance(result, tuple), "reduce() must return a tuple"
    assert len(result) == 2, "reduce() must return a 2-tuple (X_reduced, n_components)"


# ── Test 2: n_components is an int ─────────────────────────────────────────
def test_n_components_is_int():
    _, k = reduce_fn(_X_full, 0.95)
    assert isinstance(k, (int, np.integer)), (
        f"n_components must be an int, got {type(k)}"
    )


# ── Test 3: n_components matches the reference within ±1 ──────────────────
def test_n_components_matches_reference():
    _, k = reduce_fn(_X_full, 0.95)
    assert abs(int(k) - _TRUE_K_95) <= 1, (
        f"n_components={k} but reference is {_TRUE_K_95} (tolerance ±1). "
        "Make sure you use the minimum k whose cumvar >= variance."
    )


# ── Test 4: n_components < 64 (actual compression) ────────────────────────
def test_n_components_less_than_features():
    _, k = reduce_fn(_X_full, 0.95)
    assert int(k) < _X_full.shape[1], (
        f"n_components={k} must be strictly less than n_features={_X_full.shape[1]}"
    )


# ── Test 5: X_reduced has the correct shape ────────────────────────────────
def test_x_reduced_shape():
    Xr, k = reduce_fn(_X_full, 0.95)
    assert isinstance(Xr, np.ndarray), "X_reduced must be a numpy.ndarray"
    assert Xr.shape == (_X_full.shape[0], int(k)), (
        f"X_reduced.shape should be ({_X_full.shape[0]}, {k}), got {Xr.shape}"
    )


# ── Test 6: variance parameter is respected (0.90 gives fewer components) ──
def test_variance_param_respected():
    _, k90 = reduce_fn(_X_full, 0.90)
    _, k95 = reduce_fn(_X_full, 0.95)
    assert int(k90) < int(k95), (
        f"variance=0.90 should need fewer components than 0.95, "
        f"got k90={k90} vs k95={k95}"
    )


# ── Test 7: downstream accuracy on train/test split > 0.90 ─────────────────
def test_downstream_accuracy_above_threshold():
    """LogisticRegression on the reduced features must reach > 0.90 accuracy."""
    Xr, k = reduce_fn(_X_full, 0.95)
    X_train, X_test, y_train, y_test = train_test_split(
        Xr, _y_full, test_size=0.25, random_state=0
    )
    clf = LogisticRegression(max_iter=2000, random_state=0)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    assert acc > 0.90, (
        f"Held-out accuracy = {acc:.4f}; expected > 0.90. "
        "The reduced representation does not retain enough discriminative information."
    )


# ── Test 8: anti-leakage — shuffled labels collapse accuracy ───────────────
def test_anti_leakage_shuffled_labels():
    """A model trained on shuffled labels must score near chance (< 0.20)."""
    Xr, _ = reduce_fn(_X_full, 0.95)
    rng = np.random.RandomState(42)
    y_shuffled = rng.permutation(_y_full)
    X_train, X_test, y_train, y_test = train_test_split(
        Xr, _y_full, test_size=0.25, random_state=0
    )
    X_train_s, _, y_train_s, _ = train_test_split(
        Xr, y_shuffled, test_size=0.25, random_state=0
    )
    clf = LogisticRegression(max_iter=2000, random_state=0)
    clf.fit(X_train_s, y_train_s)
    acc = clf.score(X_test, y_test)
    assert acc < 0.20, (
        f"Shuffled-label accuracy = {acc:.4f}; expected < 0.20. "
        "The representation appears to encode label information beyond training."
    )


# ── Test 9: source uses PCA ────────────────────────────────────────────────
def test_source_uses_pca():
    usage = gu.source_uses(SOL, ["PCA"])
    assert usage["PCA"], (
        "solution.py must use sklearn.decomposition.PCA (or import PCA directly). "
        "A hand-rolled SVD that avoids PCA does not satisfy the contract."
    )


# ── Advisory: code quality report (never asserted) ────────────────────────
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted
