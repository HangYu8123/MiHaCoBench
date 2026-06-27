"""
solution.py — 6-step TF-IDF search-index pipeline

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Output JSON: {"step": K, "data": <result>, "provenance": "<sha256hex>"}
"""

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict


# ---------------------------------------------------------------------------
# CLI + provenance helpers
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="TF-IDF index pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-6)")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="output", required=True, help="Output JSON path")
    return parser.parse_args()


def read_input(path):
    """Read and parse the JSON input file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_provenance(in_path):
    """Compute SHA-256 hex digest of the exact bytes of the input file."""
    with open(in_path, "rb") as f:
        raw = f.read()
    return hashlib.sha256(raw).hexdigest()


def write_output(step, data, in_path, out_path):
    """Write output JSON with provenance."""
    provenance = compute_provenance(in_path)
    result = {
        "step": step,
        "data": data,
        "provenance": provenance,
    }
    encoded = json.dumps(result, ensure_ascii=False).encode("utf-8")
    with open(out_path, "wb") as f:
        f.write(encoded)


# ---------------------------------------------------------------------------
# Step 1 — tokenize
# ---------------------------------------------------------------------------

def step1_tokenize(input_json):
    """
    Read docs from the raw input (key "docs"), lowercase each doc's text,
    split on runs of non-alphanumeric chars, drop empty fragments.
    Returns {"tokens": {doc_id: [token, ...]}}
    """
    docs = input_json["docs"]  # step 1 reads the raw corpus directly
    tokens = {}
    for doc in docs:
        doc_id = doc["id"]
        text = doc["text"].lower()
        raw = re.split(r"[^a-z0-9]+", text)
        tokens[doc_id] = [t for t in raw if t]
    return {"tokens": tokens}


# ---------------------------------------------------------------------------
# Step 2 — term_counts
# ---------------------------------------------------------------------------

def step2_term_counts(prev_data):
    """
    Count occurrences of each term per document.
    Returns {"counts": {doc_id: {term: count}}}
    """
    tokens = prev_data["tokens"]
    counts = {}
    for doc_id, tok_list in tokens.items():
        counter = Counter(tok_list)
        counts[doc_id] = dict(counter)
    return {"counts": counts}


# ---------------------------------------------------------------------------
# Step 3 — doc_frequency
# ---------------------------------------------------------------------------

def step3_doc_frequency(prev_data):
    """
    For each term, count how many distinct documents contain it.
    Forward per-doc counts and corpus size.
    Returns {"df": {term: n_docs_with_term}, "counts": {...}, "n_docs": int}
    """
    counts = prev_data["counts"]
    n_docs = len(counts)
    df = defaultdict(int)
    for doc_id, term_counts in counts.items():
        for term in term_counts:
            df[term] += 1
    return {
        "df": dict(df),
        "counts": counts,
        "n_docs": n_docs,
    }


# ---------------------------------------------------------------------------
# Step 4 — tfidf
# ---------------------------------------------------------------------------

def step4_tfidf(prev_data):
    """
    Compute TF-IDF weights.
    tf = count / total_terms_in_doc
    idf = log(N / df[term])  (natural log)
    weight = round(tf * idf, 6)
    Also forward corpus idf map (each value rounded to 6 decimals).
    Returns {"tfidf": {doc_id: {term: weight}}, "idf": {term: idf_rounded}}
    """
    df = prev_data["df"]
    counts = prev_data["counts"]
    n_docs = prev_data["n_docs"]

    # Build raw idf values (unrounded, for computation accuracy)
    raw_idf = {}
    for term, doc_freq in df.items():
        raw_idf[term] = math.log(n_docs / doc_freq)

    # Build rounded idf for forwarding (storage)
    idf_rounded = {term: round(val, 6) for term, val in raw_idf.items()}

    # Compute TF-IDF per doc
    tfidf = {}
    for doc_id, term_counts in counts.items():
        total_terms = sum(term_counts.values())
        doc_weights = {}
        for term, count in term_counts.items():
            tf = count / total_terms
            # Use unrounded idf for computation, then round the weight
            weight = round(tf * raw_idf[term], 6)
            doc_weights[term] = weight
        tfidf[doc_id] = doc_weights

    return {
        "tfidf": tfidf,
        "idf": idf_rounded,
    }


# ---------------------------------------------------------------------------
# Step 5 — rank_query
# ---------------------------------------------------------------------------

QUERY = ["alpha", "beta"]


def step5_rank_query(prev_data):
    """
    Score every document against the fixed query using cosine similarity.
    Query vector: {term: 1.0 * idf[term]} for terms in QUERY that exist in idf.
    Cosine similarity = dot(q, d) / (norm(q) * norm(d)); zero-norm -> 0.0.
    Sort descending score, ascending doc_id on ties.
    Returns [[doc_id, score], ...] all scores rounded to 6 decimals.
    """
    tfidf = prev_data["tfidf"]
    idf = prev_data["idf"]

    # Build query vector (only terms present in corpus idf)
    query_vec = {term: 1.0 * idf[term] for term in QUERY if term in idf}

    # Compute query norm
    norm_q = math.sqrt(sum(v ** 2 for v in query_vec.values()))

    results = []
    for doc_id, doc_tfidf in tfidf.items():
        if norm_q == 0.0:
            score = 0.0
        else:
            # Sparse dot product
            dot = sum(query_vec[t] * doc_tfidf.get(t, 0.0) for t in query_vec)
            norm_d = math.sqrt(sum(v ** 2 for v in doc_tfidf.values()))
            if norm_d == 0.0:
                score = 0.0
            else:
                score = dot / (norm_q * norm_d)
        results.append([doc_id, round(score, 6)])

    # Sort: descending score, then ascending doc_id (lexicographic, safe for d1-d6)
    results.sort(key=lambda x: (-x[1], x[0]))
    return results


# ---------------------------------------------------------------------------
# Step 6 — top_k
# ---------------------------------------------------------------------------

def step6_top_k(prev_data):
    """
    Take the first 3 entries from step 5's ranked list.
    Returns {"top": [doc_id, ...], "scores": [score, ...]}
    """
    ranked = prev_data  # step 5 data is already [[doc_id, score], ...]
    top3 = ranked[:3]
    return {
        "top": [r[0] for r in top3],
        "scores": [r[1] for r in top3],
    }


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

STEP_FUNCS = {
    1: step1_tokenize,
    2: step2_term_counts,
    3: step3_doc_frequency,
    4: step4_tfidf,
    5: step5_rank_query,
    6: step6_top_k,
}


def main():
    args = parse_args()
    step = args.step

    if step not in STEP_FUNCS:
        print(f"Error: step must be 1-6, got {step}", file=sys.stderr)
        sys.exit(1)

    # Read input
    input_json = read_input(args.input)

    # Step 1 reads "docs" directly from raw input;
    # Steps 2-6 read "data" from the prior step's output.
    if step == 1:
        step_input = input_json
    else:
        step_input = input_json["data"]

    # Execute step
    result_data = STEP_FUNCS[step](step_input)

    # Write output
    write_output(step, result_data, args.input, args.output)


if __name__ == "__main__":
    main()
