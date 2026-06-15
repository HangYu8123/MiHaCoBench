"""Deliberately-broken reference for ml/m05_text_classification.

Planted defect: predict() always returns the majority class label from training,
ignoring the actual fitted model. This causes held-out accuracy to equal the
class prior (~0.5 for a balanced dataset) and fail the >0.85 accuracy test.
"""
from __future__ import annotations

from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def train(texts: list[str], labels: list) -> dict:
    """Fit a pipeline but also store the majority label for the broken predict."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, random_state=42, C=1.0)),
    ])
    pipeline.fit(texts, labels)
    # BUG: store the majority label instead of using the pipeline's predictions
    counts = Counter(labels)
    majority = counts.most_common(1)[0][0]
    return {"pipeline": pipeline, "majority": majority}


def predict(model, texts: list[str]) -> list:
    """BUG: always returns the majority class, ignoring model predictions."""
    # This will always return ~0.5 accuracy on a balanced dataset
    majority = model["majority"]
    return [majority] * len(texts)
