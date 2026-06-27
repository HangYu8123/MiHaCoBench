"""
Long-Horizon 11 — index_build (6 steps)
TF-IDF search-index pipeline.
"""
import argparse
import hashlib
import json
import math
import re
from collections import Counter


def load_input(path):
    """Read file bytes for provenance hash, then parse JSON."""
    raw_bytes = open(path, 'rb').read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    data = json.loads(raw_bytes)
    return data, provenance


def write_output(path, step, result):
    """Write output JSON with step, data, and provenance."""
    # provenance is computed by the caller from the input file bytes
    # This function is a no-op placeholder; see main() for actual writing
    pass


def step1_tokenize(raw):
    """Step 1: Tokenize docs. Input is docs.json with top-level 'docs' key."""
    docs = raw["docs"]
    tokens = {}
    for doc in docs:
        doc_id = doc["id"]
        text = doc["text"].lower()
        toks = re.split(r'[^a-z0-9]+', text)
        toks = [t for t in toks if t]
        tokens[doc_id] = toks
    return {"tokens": tokens}


def step2_term_counts(prev_data):
    """Step 2: Count terms per doc."""
    tokens = prev_data["tokens"]
    counts = {}
    for doc_id, toks in tokens.items():
        counts[doc_id] = dict(Counter(toks))
    return {"counts": counts}


def step3_doc_frequency(prev_data):
    """Step 3: Compute document frequency for each term."""
    counts = prev_data["counts"]
    n_docs = len(counts)
    df = {}
    for doc_id, term_counts in counts.items():
        for term in term_counts:
            df[term] = df.get(term, 0) + 1
    return {"df": df, "counts": counts, "n_docs": n_docs}


def step4_tfidf(prev_data):
    """Step 4: Compute TF-IDF weights."""
    df = prev_data["df"]
    counts = prev_data["counts"]
    n_docs = prev_data["n_docs"]

    # Compute IDF for each term
    idf = {}
    for term, doc_freq in df.items():
        idf[term] = round(math.log(n_docs / doc_freq), 6)

    # Compute TF-IDF for each doc
    tfidf = {}
    for doc_id, term_counts in counts.items():
        total_terms = sum(term_counts.values())
        tfidf[doc_id] = {}
        for term, count in term_counts.items():
            tf = count / total_terms
            weight = round(tf * idf[term], 6)
            tfidf[doc_id][term] = weight

    return {"tfidf": tfidf, "idf": idf}


def step5_rank_query(prev_data):
    """Step 5: Rank documents using cosine similarity with fixed query."""
    QUERY = ["alpha", "beta"]
    tfidf = prev_data["tfidf"]
    idf = prev_data["idf"]

    # Build query vector: tf=1 for each query term weighted by idf
    qvec = {}
    for term in QUERY:
        if term in idf:
            qvec[term] = 1.0 * idf[term]

    # Compute query norm
    norm_q = math.sqrt(sum(v ** 2 for v in qvec.values())) if qvec else 0.0

    # Score each doc by cosine similarity
    results = []
    for doc_id, dvec in tfidf.items():
        if norm_q == 0.0:
            score = 0.0
        else:
            dot = sum(qvec[t] * dvec[t] for t in qvec if t in dvec)
            norm_d = math.sqrt(sum(v ** 2 for v in dvec.values()))
            if norm_d == 0.0:
                score = 0.0
            else:
                score = dot / (norm_q * norm_d)
        results.append([doc_id, round(score, 6)])

    # Sort: descending score, ascending doc_id on ties
    results.sort(key=lambda x: (-x[1], x[0]))
    return results


def step6_top_k(prev_data):
    """Step 6: Take top 3 results from the ranking."""
    ranking = prev_data  # prev_data is the list [[doc_id, score], ...]
    top3 = ranking[:3]
    return {
        "top": [r[0] for r in top3],
        "scores": [r[1] for r in top3]
    }


def main():
    parser = argparse.ArgumentParser(description="TF-IDF index build pipeline")
    parser.add_argument('--step', type=int, required=True, help='Step number (1-6)')
    parser.add_argument('--in', dest='in_path', required=True, help='Input JSON path')
    parser.add_argument('--out', dest='out_path', required=True, help='Output JSON path')
    args = parser.parse_args()

    # Read input and compute provenance hash from raw bytes
    raw, provenance = load_input(args.in_path)

    step = args.step

    if step == 1:
        # Step 1 reads top-level "docs" key from docs.json directly
        result = step1_tokenize(raw)
    elif step == 2:
        # Steps 2+ read from prev["data"]
        prev_data = raw["data"]
        result = step2_term_counts(prev_data)
    elif step == 3:
        prev_data = raw["data"]
        result = step3_doc_frequency(prev_data)
    elif step == 4:
        prev_data = raw["data"]
        result = step4_tfidf(prev_data)
    elif step == 5:
        prev_data = raw["data"]
        result = step5_rank_query(prev_data)
    elif step == 6:
        prev_data = raw["data"]
        result = step6_top_k(prev_data)
    else:
        raise ValueError(f"Unknown step: {step}")

    output = {
        "step": step,
        "data": result,
        "provenance": provenance
    }

    with open(args.out_path, 'w') as f:
        f.write(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
