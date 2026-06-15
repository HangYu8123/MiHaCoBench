# ML 02 — `m02_regression`: Diabetes disease progression regression

**Created:** 2026-06-15 · **Category:** ml · **Weight:** 3

Train a regression model on the `sklearn.datasets.load_diabetes` dataset to
predict quantitative disease progression one year after baseline.

Write your solution as a single file `solution.py` using **scikit-learn** and
**numpy**. You may use any sklearn estimator(s) or pipeline.

## Public contract (must match exactly)

```python
def train(X: numpy.ndarray, y: numpy.ndarray) -> object:
    """Fit a regression model on the provided training data.

    Parameters
    ----------
    X : array of shape (n_samples, n_features)
        Feature matrix.
    y : array of shape (n_samples,)
        Continuous target values (disease progression scores).

    Returns
    -------
    model : any object that can be passed to ``predict``.
    """
    ...

def predict(model: object, X: numpy.ndarray) -> numpy.ndarray:
    """Return continuous predictions for X using the trained model.

    Parameters
    ----------
    model : the object returned by ``train``.
    X     : array of shape (n_samples, n_features)

    Returns
    -------
    predictions : numpy.ndarray of shape (n_samples,), dtype float64
        One predicted value per row.
    """
    ...
```

## Requirements

- `train(X, y)` must return a trained model object.
- `predict(model, X)` must return a 1-D numpy array of float predictions, one
  per sample in X.
- The model must achieve **R² > 0.30** on a held-out test set drawn from the
  diabetes dataset (test_size=0.25, random_state=0).
- No data leakage: the model must be trained only on the data provided to
  `train`. Do not access the test set inside `train` or `predict`.

## Notes

- The grader performs its own train/test split — do not hard-code split indices.
- Fixed seed: `numpy.random.seed(0)` is set by the grader before calling `train`.
- The grader also checks anti-leakage: fitting on shuffled labels must produce
  near-chance R² (< 0.05).
