# ML 06 — `multiclass_digits`: 10-Class Digit Recognition

**Created:** 2026-06-15 · **Category:** ml · **Weight:** 3

Implement a multiclass classifier for the scikit-learn bundled digits dataset.
Write your solution as `solution.py`. Use `scikit-learn` and `numpy`.

The grader will call `train` on a training split and `predict` on a held-out
test split. Do NOT do your own train/test split inside `train` — just fit a
model on whatever `(X, y)` you are given.

## Public contract (must match exactly)

```python
def train(X: numpy.ndarray, y: numpy.ndarray) -> object:
    """Fit a multiclass classifier on the provided training data and return it.

    Parameters
    ----------
    X : numpy.ndarray of shape (n_samples, n_features)
        Feature matrix (pixel values, n_features=64).
    y : numpy.ndarray of shape (n_samples,)
        Integer class labels in {0, 1, ..., 9}.

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
        Predicted integer class labels in {0, 1, ..., 9}.
    """
    ...
```

## Dataset

Use `sklearn.datasets.load_digits()` (bundled with scikit-learn; no external
data download required). The dataset has 1797 samples, 64 numeric features
(8×8 pixel images), and 10 balanced classes (digits 0–9).

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
accuracy_score(y_test, pred) > 0.95
```

A `StandardScaler` + `SVC(kernel="rbf")` or `LogisticRegression` pipeline
reliably achieves 0.97–0.99 with `random_state=42`.

## Notes

* The returned `model` object must have a `.predict` method.
* Determinism: use `random_state=42` (or any fixed seed) in your estimator so
  results are reproducible.
* Do not import the digits dataset inside `predict` — only use the model
  that was passed in.
* Labels must be integers in {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}.
