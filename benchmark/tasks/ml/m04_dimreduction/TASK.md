# ML 04 — `dimreduction`: PCA dimensionality reduction on hand-written digits

**Created:** 2026-06-15 · **Category:** ml · **Weight:** 3

Implement a single-file PCA-based dimensionality reducer for the scikit-learn
digits dataset. Write your solution as `solution.py`. Use `scikit-learn` and
`numpy` only.

## Dataset

`sklearn.datasets.load_digits()` — 1797 samples, 64 features (8×8 pixel
intensities), 10 classes (digits 0–9).

## Public contract (must match exactly)

```python
def reduce(X: np.ndarray, variance: float = 0.95) -> tuple[np.ndarray, int]:
    ...
```

**Parameters:**

* `X` — a 2-D numpy array of shape `(n_samples, 64)` containing the raw digit
  features as returned by `load_digits()`.
* `variance` — the minimum cumulative explained variance ratio to capture
  (default `0.95`). A float in `(0, 1]`.

**Returns:** a tuple `(X_reduced, n_components)` where:

* `n_components` — the **minimum** number of PCA components whose cumulative
  explained variance ratio is `>= variance`. This is a Python `int`.
* `X_reduced` — `X` projected onto those `n_components` principal components.
  Shape must be exactly `(n_samples, n_components)`. A `numpy.ndarray`.

**Implementation requirement:** use `sklearn.decomposition.PCA` internally.
The function must be deterministic: given the same `X` and `variance` it must
always return the same `n_components` and the same `X_reduced`.

## Notes

* `n_components` must equal the minimum number of PC directions needed so that
  `sum(explained_variance_ratio_[:k]) >= variance`.
* The returned array dtype does not matter as long as it is a floating-point
  `numpy.ndarray`.
* Do not hard-code a fixed number of components — it must be derived from the
  data and the `variance` argument.
