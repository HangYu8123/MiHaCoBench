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
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_output(out_path: str, step: int, data, provenance: str):
    result = {"step": step, "data": data, "provenance": provenance}
    with open(out_path, 'w') as f:
        json.dump(result, f)


# ─── Step 1: tokenize ────────────────────────────────────────────────────────

def step1_tokenize(in_path: str, out_path: str):
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        corpus = json.load(f)

    docs = corpus["docs"]
    tokens = {}
    for doc in docs:
        doc_id = doc["id"]
        text = doc["text"].lower()
        toks = re.split(r'[^a-z0-9]+', text)
        toks = [t for t in toks if t]
        tokens[doc_id] = toks

    data = {"tokens": tokens}
    write_output(out_path, 1, data, provenance)


# ─── Step 2: term_counts ─────────────────────────────────────────────────────

def step2_term_counts(in_path: str, out_path: str):
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        prev = json.load(f)

    tokens = prev["data"]["tokens"]
    counts = {}
    for doc_id, toks in tokens.items():
        term_count = {}
        for t in toks:
            term_count[t] = term_count.get(t, 0) + 1
        counts[doc_id] = term_count

    data = {"counts": counts}
    write_output(out_path, 2, data, provenance)


# ─── Step 3: doc_frequency ───────────────────────────────────────────────────

def step3_doc_frequency(in_path: str, out_path: str):
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        prev = json.load(f)

    counts = prev["data"]["counts"]
    n_docs = len(counts)
    df = {}
    for doc_id, term_count in counts.items():
        for term in term_count:
            df[term] = df.get(term, 0) + 1

    data = {"df": df, "counts": counts, "n_docs": n_docs}
    write_output(out_path, 3, data, provenance)


# ─── Step 4: tfidf ───────────────────────────────────────────────────────────

def step4_tfidf(in_path: str, out_path: str):
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        prev = json.load(f)

    df = prev["data"]["df"]
    counts = prev["data"]["counts"]
    n_docs = prev["data"]["n_docs"]
    N = n_docs

    # Compute IDF for each term (natural log), rounded to 6 decimals
    idf = {}
    for term, df_val in df.items():
        idf[term] = round(math.log(N / df_val), 6)

    # Compute TF-IDF for each doc
    tfidf = {}
    for doc_id, term_count in counts.items():
        total_terms = sum(term_count.values())
        doc_tfidf = {}
        for term, count in term_count.items():
            tf = count / total_terms
            weight = round(tf * idf[term], 6)
            doc_tfidf[term] = weight
        tfidf[doc_id] = doc_tfidf

    data = {"tfidf": tfidf, "idf": idf}
    write_output(out_path, 4, data, provenance)


# ─── Step 5: rank_query ──────────────────────────────────────────────────────

def step5_rank_query(in_path: str, out_path: str):
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        prev = json.load(f)

    tfidf = prev["data"]["tfidf"]
    idf = prev["data"]["idf"]

    QUERY = ["alpha", "beta"]

    # Build query vector: tf=1 for each query term, weighted by idf
    query_vec = {}
    for term in QUERY:
        if term in idf:
            query_vec[term] = 1 * idf[term]

    # Compute query norm
    query_norm = math.sqrt(sum(v * v for v in query_vec.values()))

    results = []
    for doc_id, doc_vec in tfidf.items():
        if not doc_vec or query_norm == 0.0:
            score = 0.0
        else:
            # dot product
            dot = 0.0
            for term, qw in query_vec.items():
                dot += qw * doc_vec.get(term, 0.0)
            doc_norm = math.sqrt(sum(v * v for v in doc_vec.values()))
            if doc_norm == 0.0:
                score = 0.0
            else:
                score = dot / (query_norm * doc_norm)
        results.append([doc_id, round(score, 6)])

    # Sort by descending score, ties by ascending doc_id
    results.sort(key=lambda x: (-x[1], x[0]))

    data = results
    write_output(out_path, 5, data, provenance)


# ─── Step 6: top_k ───────────────────────────────────────────────────────────

def step6_top_k(in_path: str, out_path: str):
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        prev = json.load(f)

    ranking = prev["data"]
    top3 = ranking[:3]

    top_ids = [entry[0] for entry in top3]
    top_scores = [entry[1] for entry in top3]

    data = {"top": top_ids, "scores": top_scores}
    write_output(out_path, 6, data, provenance)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--in', dest='in_path', required=True)
    parser.add_argument('--out', dest='out_path', required=True)
    args = parser.parse_args()

    dispatch = {
        1: step1_tokenize,
        2: step2_term_counts,
        3: step3_doc_frequency,
        4: step4_tfidf,
        5: step5_rank_query,
        6: step6_top_k,
    }

    fn = dispatch.get(args.step)
    if fn is None:
        print(f"Unknown step: {args.step}", file=sys.stderr)
        sys.exit(1)

    fn(args.in_path, args.out_path)


if __name__ == '__main__':
    main()
