"""Gold reference for ml/m05_text_classification — sports vs tech binary classifier.

Uses a TfidfVectorizer + LogisticRegression pipeline. Deterministic via fixed
random_state. Exposes the public contract: train(texts, labels) -> model,
predict(model, texts) -> labels.
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def train(texts: list[str], labels: list) -> Pipeline:
    """Fit a TF-IDF + LogisticRegression pipeline and return the trained model."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, random_state=42, C=1.0)),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict(model: Pipeline, texts: list[str]) -> list:
    """Return predicted label strings for the given texts."""
    return list(model.predict(texts))
