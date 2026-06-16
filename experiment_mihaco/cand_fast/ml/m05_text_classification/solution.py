from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def train(texts: list, labels: list) -> object:
    """Fit a classifier on texts+labels and return a trained model object."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2))),
        ("clf", LogisticRegression(random_state=42, max_iter=1000, C=1.0)),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict(model, texts: list) -> list:
    """Return predicted labels (list of str) for the given texts."""
    return list(model.predict(texts))
