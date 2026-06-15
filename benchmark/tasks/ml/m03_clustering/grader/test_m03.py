"""Grader for ml/m03_clustering. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken variant assigns all points to cluster 0 (ARI ~ 0), so any test that
checks ARI or distinct-label count will catch it.
"""
import numpy as np
import pytest
from sklearn.datasets import make_blobs
from sklearn.metrics import adjusted_rand_score

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "ml", "m03_clustering"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
fit_predict = gu.load_callable(SOL, "solution.py", "fit_predict")

# ---------------------------------------------------------------------------
# Primary dataset: 600 samples, 5 centres, 4 features, random_state=0
# ---------------------------------------------------------------------------
X_MAIN, Y_MAIN = make_blobs(
    n_samples=600, centers=5, n_features=4, random_state=0, cluster_std=1.0
)

# ---------------------------------------------------------------------------
# Secondary dataset: different seed and cluster count
# ---------------------------------------------------------------------------
X_SEC, Y_SEC = make_blobs(
    n_samples=400, centers=4, n_features=3, random_state=7, cluster_std=0.8
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_output_length_main():
    """Labels array must have the same number of elements as X."""
    labels = fit_predict(X_MAIN, 5)
    assert len(labels) == 600


def test_distinct_labels_main():
    """Exactly n_clusters distinct labels must appear in the output."""
    labels = fit_predict(X_MAIN, 5)
    assert len(set(labels.tolist())) == 5


def test_ari_threshold_main():
    """Adjusted rand score on the primary blob dataset must exceed 0.85."""
    labels = fit_predict(X_MAIN, 5)
    ari = adjusted_rand_score(Y_MAIN, labels)
    assert ari > 0.85, f"ARI={ari:.4f} is below the 0.85 threshold"


def test_output_length_secondary():
    """Output length matches n_samples on the secondary dataset."""
    labels = fit_predict(X_SEC, 4)
    assert len(labels) == 400


def test_distinct_labels_secondary():
    """Exactly n_clusters=4 distinct labels on the secondary dataset."""
    labels = fit_predict(X_SEC, 4)
    assert len(set(labels.tolist())) == 4


def test_ari_threshold_secondary():
    """Adjusted rand score on the secondary blob dataset must exceed 0.85."""
    labels = fit_predict(X_SEC, 4)
    ari = adjusted_rand_score(Y_SEC, labels)
    assert ari > 0.85, f"ARI={ari:.4f} is below the 0.85 threshold"


def test_label_dtype_is_integer():
    """Returned labels must be integer dtype (not float)."""
    labels = fit_predict(X_MAIN, 5)
    assert np.issubdtype(labels.dtype, np.integer), (
        f"expected integer dtype, got {labels.dtype}"
    )


def test_anti_leakage_mislabelled():
    """Anti-leakage sanity: shuffled 'true' labels should not improve ARI.

    The adjusted_rand_score between the model's output and a randomly permuted
    label vector should stay near 0, confirming the model actually clusters X
    rather than memorising or leaking true labels.
    """
    rng = np.random.default_rng(99)
    shuffled_y = rng.permutation(Y_MAIN)
    labels = fit_predict(X_MAIN, 5)
    ari_shuffled = adjusted_rand_score(shuffled_y, labels)
    # A genuinely correct clustering will have low ARI against random labels
    assert ari_shuffled < 0.5, (
        f"ARI against shuffled labels={ari_shuffled:.4f} unexpectedly high"
    )


@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory code-quality report — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
