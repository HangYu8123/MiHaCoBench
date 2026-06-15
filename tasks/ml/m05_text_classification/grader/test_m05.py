"""Grader for ml/m05_text_classification. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference always predicts the majority class, so it fails the
>0.85 held-out accuracy test. All other tests use properties of a real classifier.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "ml", "m05_text_classification"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the committed dataset once at module level (deterministic, never regenerated)
_DATA_PATH = (
    gu.PYBENCH_ROOT / "tasks" / CATEGORY / TASK_ID / "data" / "texts.csv"
)
_df = pd.read_csv(_DATA_PATH)
_TEXTS = _df["text"].tolist()
_LABELS = _df["label"].tolist()

# The grader owns the split — fixed seeds, stratified
_X_TRAIN, _X_TEST, _Y_TRAIN, _Y_TEST = train_test_split(
    _TEXTS, _LABELS, test_size=0.25, random_state=0, stratify=_LABELS
)

# Load solution callables
_train = gu.load_callable(SOL, "solution.py", "train")
_predict = gu.load_callable(SOL, "solution.py", "predict")

# Fit the model once; reuse across tests
_MODEL = _train(_X_TRAIN, _Y_TRAIN)


# ---------------------------------------------------------------------------
# Test 1: train returns something (model is not None)
# ---------------------------------------------------------------------------
def test_train_returns_model():
    """train() must return a non-None model object."""
    assert _MODEL is not None


# ---------------------------------------------------------------------------
# Test 2: predict output shape and type
# ---------------------------------------------------------------------------
def test_predict_output_shape():
    """predict() must return a list of the same length as the input."""
    preds = _predict(_MODEL, _X_TEST)
    assert isinstance(preds, list), "predict must return a list"
    assert len(preds) == len(_X_TEST), (
        f"predict returned {len(preds)} labels for {len(_X_TEST)} inputs"
    )


# ---------------------------------------------------------------------------
# Test 3: predict output values are valid label strings
# ---------------------------------------------------------------------------
def test_predict_output_labels():
    """All predicted labels must be 'sports' or 'tech'."""
    preds = _predict(_MODEL, _X_TEST)
    valid = {"sports", "tech"}
    bad = [p for p in preds if p not in valid]
    assert not bad, f"Invalid predicted labels found: {bad[:5]}"


# ---------------------------------------------------------------------------
# Test 4: held-out accuracy > 0.85
# ---------------------------------------------------------------------------
def test_held_out_accuracy():
    """Classifier must achieve > 0.85 accuracy on the held-out test set."""
    preds = _predict(_MODEL, _X_TEST)
    acc = accuracy_score(_Y_TEST, preds)
    assert acc > 0.85, f"Held-out accuracy {acc:.4f} is not > 0.85"


# ---------------------------------------------------------------------------
# Test 5: anti-leakage — shuffled labels drop accuracy toward chance (< 0.70)
# ---------------------------------------------------------------------------
def test_shuffled_labels_near_chance():
    """Training on randomly shuffled labels must yield < 0.70 accuracy."""
    rng = np.random.default_rng(99)
    shuffled = rng.permutation(_Y_TRAIN).tolist()
    model_shuffled = _train(_X_TRAIN, shuffled)
    preds = _predict(model_shuffled, _X_TEST)
    acc = accuracy_score(_Y_TEST, preds)
    assert acc < 0.70, (
        f"Accuracy {acc:.4f} after label shuffle is unexpectedly high (>= 0.70); "
        "possible leakage or trivial majority-class predictor"
    )


# ---------------------------------------------------------------------------
# Test 6: single-example prediction works (no batch-size assumption)
# ---------------------------------------------------------------------------
def test_predict_single_example():
    """predict() must work correctly on a single-element list."""
    single_sports = ["The champion athlete won the national tournament."]
    single_tech = ["The developer deployed the new cloud-based software."]
    pred_s = _predict(_MODEL, single_sports)
    pred_t = _predict(_MODEL, single_tech)
    assert len(pred_s) == 1
    assert len(pred_t) == 1
    assert pred_s[0] in {"sports", "tech"}
    assert pred_t[0] in {"sports", "tech"}


# ---------------------------------------------------------------------------
# Test 7: surface-form constraint — TfidfVectorizer must be used
# ---------------------------------------------------------------------------
def test_source_uses_tfidf():
    """Solution source must reference TfidfVectorizer ('Tfidf' substring)."""
    usage = gu.source_uses(SOL, ["Tfidf"])
    assert usage["Tfidf"], (
        "Solution must use TfidfVectorizer; 'Tfidf' not found in source"
    )


# ---------------------------------------------------------------------------
# Test 8: model is reusable — predict twice gives same results
# ---------------------------------------------------------------------------
def test_predict_deterministic():
    """Calling predict twice on the same model must return identical results."""
    preds1 = _predict(_MODEL, _X_TEST)
    preds2 = _predict(_MODEL, _X_TEST)
    assert preds1 == preds2, "predict is not deterministic — got different results on same input"


# ---------------------------------------------------------------------------
# Advisory: code quality (never gates pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted
