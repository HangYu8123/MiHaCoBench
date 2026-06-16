"""
6-step TF-IDF search-index pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import math
import re
import sys


def compute_provenance(in_path: str) -> str:
    """Compute SHA-256 hex digest of the input file bytes."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_output(out_path: str, step: int, data, provenance: str):
    """Write the standard output JSON."""
    result = {"step": step, "data": data, "provenance": provenance}
    with open(out_path, "w") as f:
        json.dump(result, f)


def tokenize(text: str):
    """Lowercase and split on runs of non-alphanumeric characters."""
    lowered = text.lower()
    tokens = re.split(r"[^a-z0-9]+", lowered)
    # Drop empty fragments
    return [t for t in tokens if t]


def step1_tokenize(in_data: dict) -> dict:
    """Step 1: tokenize each doc's text."""
    docs = in_data["docs"]
    tokens = {}
    for doc in docs:
        doc_id = doc["id"]
        text = doc["text"]
        tokens[doc_id] = tokenize(text)
    return {"tokens": tokens}


def step2_term_counts(in_data: dict) -> dict:
    """Step 2: compute term counts per document."""
    tokens = in_data["tokens"]
    counts = {}
    for doc_id, toks in tokens.items():
        term_count = {}
        for tok in toks:
            term_count[tok] = term_count.get(tok, 0) + 1
        counts[doc_id] = term_count
    return {"counts": counts}


def step3_doc_frequency(in_data: dict) -> dict:
    """Step 3: compute document frequency for each term."""
    counts = in_data["counts"]
    n_docs = len(counts)
    df = {}
    for doc_id, term_count in counts.items():
        for term in term_count:
            df[term] = df.get(term, 0) + 1
    return {"df": df, "counts": counts, "n_docs": n_docs}


def step4_tfidf(in_data: dict) -> dict:
    """Step 4: compute TF-IDF weights."""
    df = in_data["df"]
    counts = in_data["counts"]
    n_docs = in_data["n_docs"]

    # Compute IDF for each term: log(N / df[term]), natural log
    idf = {}
    for term, df_count in df.items():
        idf[term] = round(math.log(n_docs / df_count), 6)

    # Compute TF-IDF for each doc
    tfidf = {}
    for doc_id, term_count in counts.items():
        total_terms = sum(term_count.values())
        doc_tfidf = {}
        for term, count in term_count.items():
            tf = count / total_terms
            weight = tf * idf[term]
            doc_tfidf[term] = round(weight, 6)
        tfidf[doc_id] = doc_tfidf

    return {"tfidf": tfidf, "idf": idf}


def cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """Compute cosine similarity between two sparse vectors."""
    # Dot product
    dot = 0.0
    for term, weight in vec_a.items():
        if term in vec_b:
            dot += weight * vec_b[term]

    # Norms
    norm_a = math.sqrt(sum(w * w for w in vec_a.values()))
    norm_b = math.sqrt(sum(w * w for w in vec_b.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


def step5_rank_query(in_data: dict) -> list:
    """Step 5: rank documents by cosine similarity with the fixed query."""
    QUERY = ["alpha", "beta"]

    tfidf = in_data["tfidf"]
    idf = in_data["idf"]

    # Build query vector: query term tf = 1, weighted by corpus idf
    query_vec = {}
    for term in QUERY:
        if term in idf:
            query_vec[term] = idf[term]

    # Score each doc
    scores = []
    for doc_id, doc_vec in tfidf.items():
        score = cosine_similarity(query_vec, doc_vec)
        scores.append([doc_id, round(score, 6)])

    # Sort by descending score, ties broken by ascending doc_id
    scores.sort(key=lambda x: (-x[1], x[0]))

    return scores


def step6_top_k(in_data: list) -> dict:
    """Step 6: take the top 3 entries from the ranking."""
    top3 = in_data[:3]
    top_ids = [entry[0] for entry in top3]
    top_scores = [entry[1] for entry in top3]
    return {"top": top_ids, "scores": top_scores}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Compute provenance before reading JSON
    provenance = compute_provenance(in_path)

    with open(in_path, "r") as f:
        in_json = json.load(f)

    # Step 1 reads from the raw docs JSON (has "docs" key)
    # Steps 2-6 read from the previous step's output (has "data" key)
    if step == 1:
        in_data = in_json
    else:
        in_data = in_json["data"]

    if step == 1:
        result = step1_tokenize(in_data)
    elif step == 2:
        result = step2_term_counts(in_data)
    elif step == 3:
        result = step3_doc_frequency(in_data)
    elif step == 4:
        result = step4_tfidf(in_data)
    elif step == 5:
        result = step5_rank_query(in_data)
    elif step == 6:
        result = step6_top_k(in_data)
    else:
        print(f"Unknown step: {step}", file=sys.stderr)
        sys.exit(1)

    write_output(out_path, step, result, provenance)


if __name__ == "__main__":
    main()
