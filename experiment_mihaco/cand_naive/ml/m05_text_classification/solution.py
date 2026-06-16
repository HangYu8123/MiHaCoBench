"""
Binary text classifier: sports vs tech.
Uses TfidfVectorizer + LogisticRegression wrapped in a Pipeline.
"""

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def train(texts: list[str], labels: list) -> object:
    """Fit a classifier on texts+labels and return a trained model object."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            C=5.0,
            max_iter=1000,
            random_state=42,
            solver="lbfgs",
        )),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict(model, texts: list[str]) -> list:
    """Return predicted labels (list of str) for the given texts."""
    return list(model.predict(texts))
