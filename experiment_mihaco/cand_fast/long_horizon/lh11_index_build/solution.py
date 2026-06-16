"""
Long-Horizon 11 — index_build (6 steps)
TF-IDF search-index pipeline. Stdlib only.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import json
import hashlib
import re
import math
import collections


def compute_provenance(in_path):
    """Compute sha256 of the exact bytes of the --in file."""
    with open(in_path, 'rb') as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()


def write_output(out_path, step, data, provenance):
    """Write the output JSON envelope."""
    result = {"step": step, "data": data, "provenance": provenance}
    with open(out_path, 'w') as f:
        json.dump(result, f)


def step1_tokenize(prev):
    """
    Step 1: tokenize each doc's text.
    Input: prev["docs"] = [{"id": ..., "text": ...}, ...]
    Output: {"tokens": {doc_id: [tokens]}}
    """
    docs = prev["docs"]
    tokens = {}
    for doc in docs:
        doc_id = doc["id"]
        text = doc["text"]
        raw = re.split(r'[^a-z0-9]+', text.lower())
        tok_list = [t for t in raw if t]
        tokens[doc_id] = tok_list
    return {"tokens": tokens}


def step2_term_counts(prev):
    """
    Step 2: count term occurrences per doc.
    Input: prev["tokens"] = {doc_id: [tokens]}
    Output: {"counts": {doc_id: {term: count}}}
    """
    tokens = prev["tokens"]
    counts = {}
    for doc_id, tok_list in tokens.items():
        counter = collections.Counter(tok_list)
        counts[doc_id] = dict(counter)
    return {"counts": counts}


def step3_doc_frequency(prev):
    """
    Step 3: compute document frequency of each term.
    A document counts at most once per term.
    Input: prev["counts"] = {doc_id: {term: count}}
    Output: {"df": {term: n_docs}, "counts": {...}, "n_docs": int}
    """
    counts = prev["counts"]
    df = collections.Counter()
    for doc_id, term_dict in counts.items():
        # Use set of terms in this doc (each doc counted at most once per term)
        for term in set(term_dict.keys()):
            df[term] += 1
    n_docs = len(counts)
    return {"df": dict(df), "counts": counts, "n_docs": n_docs}


def step4_tfidf(prev):
    """
    Step 4: compute TF-IDF weights.
    tf = count / total_terms_in_doc
    idf = log(N / df[term])  (natural log)
    Round each weight and each idf value to 6 decimals.
    Input: prev["df"], prev["counts"], prev["n_docs"]
    Output: {"tfidf": {doc_id: {term: weight}}, "idf": {term: idf_rounded}}
    """
    df = prev["df"]
    counts = prev["counts"]
    N = prev["n_docs"]

    # Compute idf for each term
    idf = {}
    for term, doc_count in df.items():
        idf_val = math.log(N / doc_count)
        idf[term] = round(idf_val, 6)

    # Compute tfidf per doc
    tfidf = {}
    for doc_id, term_dict in counts.items():
        total_terms = sum(term_dict.values())
        doc_tfidf = {}
        for term, count in term_dict.items():
            tf = count / total_terms
            weight = tf * idf[term]
            doc_tfidf[term] = round(weight, 6)
        tfidf[doc_id] = doc_tfidf

    return {"tfidf": tfidf, "idf": idf}


def step5_rank_query(prev):
    """
    Step 5: rank documents using cosine similarity with a fixed query.
    QUERY = ["alpha", "beta"]
    Query tf = 1 for each query term (weighted by idf).
    Output: [[doc_id, score], ...] sorted by descending score, ascending doc_id.
    Scores rounded to 6 decimals.
    """
    QUERY = ["alpha", "beta"]
    tfidf = prev["tfidf"]
    idf = prev["idf"]

    # Build query vector: {term: 1 * idf[term]} for terms in query that appear in corpus
    query_vec = {}
    for term in QUERY:
        if term in idf:
            query_vec[term] = 1.0 * idf[term]

    # Compute query norm
    q_norm = math.sqrt(sum(v ** 2 for v in query_vec.values()))

    ranking = []
    for doc_id, doc_vec in tfidf.items():
        # Dot product of query vector and doc vector
        dot = sum(query_vec.get(term, 0.0) * doc_vec.get(term, 0.0)
                  for term in query_vec)
        # Doc norm
        d_norm = math.sqrt(sum(v ** 2 for v in doc_vec.values()))

        if q_norm == 0.0 or d_norm == 0.0:
            score = 0.0
        else:
            score = dot / (q_norm * d_norm)

        score = round(score, 6)
        ranking.append([doc_id, score])

    # Sort by descending score, then ascending doc_id
    ranking.sort(key=lambda x: (-x[1], x[0]))

    return ranking


def step6_top_k(prev):
    """
    Step 6: take the first 3 entries of the step 5 ranking.
    Input: prev is the [[doc_id, score], ...] list from step 5.
    Output: {"top": [doc_id, ...], "scores": [score, ...]}
    """
    ranking = prev  # step 5's data is directly the ranking list
    top3 = ranking[:3]
    return {
        "top": [entry[0] for entry in top3],
        "scores": [entry[1] for entry in top3]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--in', dest='in_path', required=True)
    parser.add_argument('--out', dest='out_path', required=True)
    args = parser.parse_args()

    # Compute provenance from the raw bytes of the input file
    provenance = compute_provenance(args.in_path)

    # Read the JSON input
    with open(args.in_path, 'r') as f:
        prev = json.load(f)

    step = args.step

    if step == 1:
        # Step 1 reads prev["docs"]
        data = step1_tokenize(prev)
    elif step == 2:
        # Steps 2-6 read prev["data"]
        data = step2_term_counts(prev["data"])
    elif step == 3:
        data = step3_doc_frequency(prev["data"])
    elif step == 4:
        data = step4_tfidf(prev["data"])
    elif step == 5:
        data = step5_rank_query(prev["data"])
    elif step == 6:
        data = step6_top_k(prev["data"])
    else:
        raise ValueError(f"Unknown step: {step}")

    write_output(args.out_path, step, data, provenance)


if __name__ == '__main__':
    main()
