import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('reg', Ridge(alpha=1.0, random_state=0))
    ])
    model.fit(X, y)
    return model


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
    predictions = model.predict(X)
    return predictions.ravel().astype(np.float64)
