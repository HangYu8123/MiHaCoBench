"""Gold reference for long_horizon/lh11_index_build.

A 6-step TF-IDF search-index pipeline driven as a single ``solution.py`` that
dispatches on ``--step K --in <prev> --out <out>``. Each step reads ONLY the
artifact written by the previous step (step 1 reads the committed seed corpus)
and writes JSON of the shape::

    {"step": K, "data": <result>, "provenance": "<sha256 hex of the --in file>"}

so the grader can verify the provenance chain link by link. Because a later step
consumes only the previous artifact, each step's ``data`` carries the running
pipeline state (the primary field plus whatever downstream steps still need), and
an error in one step cascades into every step after it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re

# The query is a fixed constant embedded in the pipeline (step 5).
QUERY = ["alpha", "beta"]

# Round float maps to this many decimals for cross-platform stability.
ROUND = 6

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def step1_tokenize(prev: dict) -> dict:
    """Lowercase each doc text and split on runs of non-alphanumeric chars.

    Primary field ``tokens = {doc_id: [tokens]}`` (empty fragments dropped).
    """
    tokens: dict[str, list[str]] = {}
    for doc in prev["docs"]:
        toks = [t for t in _TOKEN_SPLIT.split(doc["text"].lower()) if t]
        tokens[doc["id"]] = toks
    return {"tokens": tokens}


def step2_term_counts(prev: dict) -> dict:
    """Primary field ``counts = {doc_id: {term: count}}`` from step 1's tokens."""
    counts: dict[str, dict[str, int]] = {}
    for doc_id, toks in prev["data"]["tokens"].items():
        c: dict[str, int] = {}
        for tok in toks:
            c[tok] = c.get(tok, 0) + 1
        counts[doc_id] = c
    return {"counts": counts}


def step3_doc_frequency(prev: dict) -> dict:
    """Primary field ``df = {term: number_of_DOCUMENTS containing term}``.

    A document counts at most once per term regardless of repeats inside it. The
    per-doc counts and doc total are forwarded so step 4 can compute tf-idf.
    """
    counts = prev["data"]["counts"]
    df: dict[str, int] = {}
    for term_counts in counts.values():
        for term in term_counts:  # each term counted once per document
            df[term] = df.get(term, 0) + 1
    return {"df": df, "counts": counts, "n_docs": len(counts)}


def step4_tfidf(prev: dict) -> dict:
    """Primary field ``tfidf = {doc_id: {term: tf * idf}}`` (rounded).

    ``tf = count / total_terms_in_doc`` and ``idf = log(N / df[term])`` with N the
    number of docs and natural log. The corpus ``idf`` map is forwarded for the
    query vector in step 5.
    """
    counts = prev["data"]["counts"]
    df = prev["data"]["df"]
    n_docs = prev["data"]["n_docs"]
    tfidf: dict[str, dict[str, float]] = {}
    for doc_id, term_counts in counts.items():
        total = sum(term_counts.values())
        weights: dict[str, float] = {}
        for term, c in term_counts.items():
            tf = (c / total) if total else 0.0
            idf = math.log(n_docs / df[term])
            weights[term] = round(tf * idf, ROUND)
        tfidf[doc_id] = weights
    idf_map = {term: round(math.log(n_docs / d), ROUND) for term, d in df.items()}
    return {"tfidf": tfidf, "idf": idf_map}


def step5_rank_query(prev: dict) -> list:
    """Rank docs by cosine similarity to the fixed ``QUERY`` (tf-idf weighted).

    The query vector uses query-term tf = 1 times the corpus idf for that term;
    docs use their step-4 tf-idf vectors. Returns a list of ``[doc_id, score]``
    sorted by descending score, ties broken by ascending doc_id; scores rounded.
    """
    tfidf = prev["data"]["tfidf"]
    idf = prev["data"]["idf"]

    qvec: dict[str, float] = {}
    for term in QUERY:
        qvec[term] = qvec.get(term, 0.0) + idf.get(term, 0.0)
    q_norm = math.sqrt(sum(v * v for v in qvec.values()))

    ranked: list[list] = []
    for doc_id, dvec in tfidf.items():
        dot = sum(qvec.get(term, 0.0) * w for term, w in dvec.items())
        d_norm = math.sqrt(sum(w * w for w in dvec.values()))
        if q_norm == 0.0 or d_norm == 0.0:
            score = 0.0
        else:
            score = dot / (q_norm * d_norm)
        ranked.append([doc_id, round(score, ROUND)])

    ranked.sort(key=lambda pair: (-pair[1], pair[0]))
    return ranked


def step6_top_k(prev: dict) -> dict:
    """Primary field ``{"top": [first 3 doc ids], "scores": [their 3 scores]}``."""
    ranked = prev["data"]
    top = [pair[0] for pair in ranked[:3]]
    scores = [pair[1] for pair in ranked[:3]]
    return {"top": top, "scores": scores}


STEPS = {
    1: step1_tokenize,
    2: step2_term_counts,
    3: step3_doc_frequency,
    4: step4_tfidf,
    5: step5_rank_query,
    6: step6_top_k,
}


def run_step(step: int, prev):
    """Dispatch to the transform for ``step``."""
    return STEPS[step](prev)


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = run_step(args.step, prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
