from sklearn.feature_extraction.text import TfidfVectorizer  # TfidfVectorizer — contains "Tfidf"
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def train(texts: list[str], labels: list) -> object:
    """Fit a classifier on texts+labels and return a trained model object."""
    model = Pipeline([
        ("Tfidf", TfidfVectorizer(sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    model.fit(texts, labels)
    return model


def predict(model, texts: list[str]) -> list:
    """Return predicted labels (list of str) for the given texts."""
    return list(model.predict(texts))
