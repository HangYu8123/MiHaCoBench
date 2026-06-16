"""
Binary text classifier: sports vs. tech.

Public contract:
  train(texts: list[str], labels: list) -> object
  predict(model, texts: list[str]) -> list
"""

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def train(texts: list, labels: list) -> object:
    """Fit a classifier on texts+labels and return a trained model object."""
    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                    strip_accents="unicode",
                    analyzer="word",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    random_state=42,
                    max_iter=1000,
                    C=1.0,
                ),
            ),
        ]
    )
    pipeline.fit(texts, labels)
    return pipeline


def predict(model, texts: list) -> list:
    """Return predicted labels (list of str) for the given texts."""
    return [str(x) for x in model.predict(texts)]
