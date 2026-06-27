from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def train(texts: list[str], labels: list) -> object:
    """Fit a classifier on texts+labels and return a trained model object."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_df=0.95, min_df=1)),
        ("clf", LogisticRegression(random_state=42, max_iter=1000)),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict(model, texts: list[str]) -> list:
    """Return predicted labels (list of str) for the given texts."""
    return model.predict(texts).tolist()
