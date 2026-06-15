# ML 01 — `tabular_classification`: Binary Classification on Breast Cancer Dataset

**Created:** 2026-06-15 · **Category:** ml · **Weight:** 3

Implement a binary classifier for the scikit-learn breast cancer dataset.
Write your solution as `solution.py`. Use `scikit-learn` and `numpy`.

The grader will call `train` on a training split and `predict` on a held-out
test split. Do NOT do your own train/test split inside `train` — just fit a
model on whatever `(X, y)` you are given.

## Public contract (must match exactly)

```python
def train(X: numpy.ndarray, y: numpy.ndarray) -> object:
    """Fit a classifier on the provided training data and return it.

    Parameters
    ----------
    X : numpy.ndarray of shape (n_samples, n_features)
        Feature matrix.
    y : numpy.ndarray of shape (n_samples,)
        Integer class labels (0 or 1).

    Returns
    -------
    model : object
        A fitted estimator that exposes a `predict(X)` method.
    """
    ...

def predict(model: object, X: numpy.ndarray) -> numpy.ndarray:
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
    """
    ...
```

## Dataset

Use `sklearn.datasets.load_breast_cancer()` (bundled with scikit-learn; no
external data download required). The dataset has 569 samples and 30 numeric
features for binary classification (malignant = 0, benign = 1).

## Performance requirement

The grader splits the dataset with:

```python
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=0, stratify=y
)
```

After calling `model = train(X_train, y_train)` and `pred = predict(model, X_test)`,
the grader asserts:

```python
accuracy_score(y_test, pred) > 0.92
```

## Notes

* The returned `model` object must have a `.predict` method.
* Determinism: use `random_state=42` (or any fixed seed) in your estimator so
  results are reproducible.
* Do not import the breast cancer dataset inside `predict` — only use the model
  that was passed in.
