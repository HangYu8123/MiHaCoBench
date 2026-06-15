# ML 03 — `m03_clustering`: K-Means clustering with a known number of clusters

**Created:** 2026-06-15 · **Category:** ml · **Weight:** 3

Implement a clustering solution in a single file `solution.py`.
Use **scikit-learn** and **numpy** (other packages from `requirements.txt` are allowed
but not necessary).

## Public contract (must match exactly)

```python
def fit_predict(X: np.ndarray, n_clusters: int) -> np.ndarray:
    ...
```

`X` is a 2-D float array of shape `(n_samples, n_features)`.  
`n_clusters` is the **true** number of clusters in the data (the grader always
provides this so you do not need to determine it automatically).

**Returns:** a 1-D integer array of shape `(n_samples,)` where each element is
the cluster id assigned to the corresponding sample. Cluster ids must be integers
in the range `[0, n_clusters - 1]`. The assignment of cluster ids to actual
clusters is arbitrary (label permutation is fine — the grader uses
`sklearn.metrics.adjusted_rand_score` which is permutation-invariant).

## Notes

* Determinism: the grader uses fixed seeds; your implementation should also
  use a fixed random state so repeated calls on the same input return the same
  labels.
* The grader calls `fit_predict(X, n_clusters)` directly; there is no CLI.
* No fitted state needs to persist between calls — each call to `fit_predict`
  is independent.
* The grader asserts `adjusted_rand_score(y_true, labels) > 0.85` on
  well-separated blob data; a standard K-Means implementation easily exceeds
  this threshold.
