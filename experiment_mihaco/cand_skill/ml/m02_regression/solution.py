import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge


def train(X: np.ndarray, y: np.ndarray) -> object:
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
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('reg', Ridge(alpha=1.0)),
    ])
    pipeline.fit(X, y)
    return pipeline


def predict(model: object, X: np.ndarray) -> np.ndarray:
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
    return model.predict(X).astype(np.float64).ravel()


if __name__ == "__main__":
    # Self-validation block — runs only when executed directly, not when imported.
    from sklearn.datasets import load_diabetes
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score

    data = load_diabetes()
    X_all, y_all = data.data, data.target

    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.25, random_state=0
    )

    # Task 2 verification: train returns a Pipeline
    model = train(X_train, y_train)
    assert isinstance(model, Pipeline), "train() must return a Pipeline"

    # Task 3 verification: predict returns 1-D float64 array
    preds = predict(model, X_test)
    assert isinstance(preds, np.ndarray), "predict() must return a numpy.ndarray"
    assert preds.shape == (X_test.shape[0],), f"Wrong shape: {preds.shape}"
    assert preds.dtype == np.float64, f"Wrong dtype: {preds.dtype}"

    # Task 4 verification: R² > 0.30
    r2 = r2_score(y_test, preds)
    print(f"R² on held-out test set: {r2:.4f}")
    assert r2 > 0.30, f"R² = {r2:.4f} is below 0.30 threshold"

    # Anti-leakage smoke-test: shuffled labels must yield R² < 0.05
    rng = np.random.RandomState(42)
    y_shuffled = rng.permutation(y_train)
    model_shuffled = train(X_train, y_shuffled)
    preds_shuffled = predict(model_shuffled, X_test)
    r2_shuffled = r2_score(y_test, preds_shuffled)
    print(f"R² on shuffled-label model: {r2_shuffled:.4f}")
    assert r2_shuffled < 0.05, f"Anti-leakage check failed: R² = {r2_shuffled:.4f}"

    print("All self-validation checks passed.")
