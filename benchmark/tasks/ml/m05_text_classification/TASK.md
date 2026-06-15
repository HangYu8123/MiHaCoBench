# ML 05 — `text_classification`: binary text classification (sports vs tech)

**Created:** 2026-06-15 · **Category:** ml · **Weight:** 3

Implement a binary text classifier that distinguishes "sports" articles from "tech"
articles. Write your solution as a single file `solution.py`. You may use
`scikit-learn` (and numpy/pandas as helpers).

A labeled dataset of 130 short sentences is committed to
`data/texts.csv` (columns: `text`, `label`; labels are the strings `"sports"` or
`"tech"`). Do **not** commit that CSV yourself — it is provided.

## Public contract (must match exactly)

```python
def train(texts: list[str], labels: list) -> object:
    """Fit a classifier on texts+labels and return a trained model object."""
    ...

def predict(model, texts: list[str]) -> list:
    """Return predicted labels (list of str) for the given texts."""
    ...
```

* `train` receives a list of raw text strings and a parallel list of label strings
  (`"sports"` or `"tech"`). It must return a fitted model (e.g. a
  `sklearn.pipeline.Pipeline` wrapping a `TfidfVectorizer` and a classifier).
* `predict` receives the model returned by `train` and a list of raw text strings.
  It must return a list of predicted label strings (same order, same length).

### Required internal technique

Your solution **must** use `TfidfVectorizer` (from `sklearn.feature_extraction.text`).
The grader checks that the string `"Tfidf"` appears in your source.

### Determinism

If your classifier uses randomness, fix its `random_state` (e.g. `random_state=42`).

## Notes

* The grader performs its **own** train/test split (test_size=0.25, random_state=0,
  stratified). Your solution must achieve >0.85 accuracy on the held-out set.
* An anti-leakage check will also verify that training on randomly-shuffled labels
  causes accuracy to drop toward chance (< 0.70).
* Float comparisons use tolerances; no rounding needed.
