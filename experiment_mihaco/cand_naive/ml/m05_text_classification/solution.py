"""
Binary text classifier: sports vs tech.
Uses TfidfVectorizer + LogisticRegression pipeline.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def train(texts: list[str], labels: list) -> object:
    """Fit a classifier on texts+labels and return a trained model object."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=10000,
            sublinear_tf=True,
            min_df=1,
        )),
        ("clf", LogisticRegression(
            random_state=42,
            max_iter=1000,
            C=1.0,
        )),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict(model, texts: list[str]) -> list:
    """Return predicted labels (list of str) for the given texts."""
    return list(model.predict(texts))
