# Long-Horizon 11 — `index_build` (6 steps)

**Created:** 2026-06-16 · **Category:** long_horizon · **Horizon:** 6 steps · **Weight:** 3

Build a **6-step TF-IDF search-index pipeline** as a single file `solution.py`.
Each step is run separately and **consumes only the artifact written by the
previous step** — you may not re-read the original corpus from a later step.
Stdlib only.

## CLI contract (identical for every step)

```
python solution.py --step <K> --in <input_json_path> --out <output_json_path>
```

Each step reads the JSON at `--in`, computes its result, and writes to `--out` a
JSON object with **exactly** these keys:

```json
{"step": <K>, "data": <result>, "provenance": "<sha256 hex of the EXACT bytes of the --in file>"}
```

`provenance` is `hashlib.sha256(open(in_path,'rb').read()).hexdigest()`. The grader
verifies it, so step *K* must genuinely read the file produced by step *K-1*.

Because a later step consumes only the previous artifact, each step's `data`
carries the **running pipeline state** (the step's primary result plus whatever
downstream steps still need). An error in one step therefore cascades into every
step after it.

## The chain

* **Input** (`data/docs.json`, given): a fixed corpus of 6 short documents:
  `{"docs": [{"id": "d1", "text": "..."}, ...]}` with deliberate term overlap and
  intra-document repeats so ranking is non-trivial. Step 1 reads `prev["docs"]`;
  every later step reads `prev["data"]`.

* **Step 1 — `tokenize`:** lowercase each doc's `text` and split on runs of
  non-alphanumeric characters (regex `[^a-z0-9]+`), dropping empty fragments.
  `data = {"tokens": {doc_id: [tokens]}}`.

* **Step 2 — `term_counts`:** from step 1's tokens.
  `data = {"counts": {doc_id: {term: count}}}`.

* **Step 3 — `doc_frequency`:** the number of **documents** containing each term —
  a document counts **at most once per term** regardless of how many times the term
  repeats inside it. Forward the per-doc counts and corpus size for later steps.
  `data = {"df": {term: n_documents}, "counts": {doc_id: {term: count}}, "n_docs": <int>}`.

* **Step 4 — `tfidf`:** for each doc, `weight = tf * idf` where
  `tf = count / total_terms_in_doc` and `idf = log(N / df[term])` with `N = n_docs`
  and **natural log**; round each weight to **6 decimals**. Also forward the corpus
  `idf` map (each value rounded to 6 decimals) for the query in step 5.
  `data = {"tfidf": {doc_id: {term: round(tf*idf, 6)}}, "idf": {term: round(idf, 6)}}`.

* **Step 5 — `rank_query`:** a **fixed query** is embedded in the step-5 code:
  `QUERY = ["alpha", "beta"]`. Build the query vector with query-term `tf = 1`
  weighted by that term's corpus `idf`, then score every doc by **cosine
  similarity** between the query vector and the doc's step-4 tf-idf vector.
  `data = [[doc_id, score], ...]` sorted by **descending score**, ties broken by
  **ascending doc_id**; scores rounded to **6 decimals**. A doc with an empty
  vector (or a zero-norm query) scores `0.0`.

* **Step 6 — `top_k`:** take the first 3 entries of step 5's ranking.
  `data = {"top": [doc_id, doc_id, doc_id], "scores": [s1, s2, s3]}`.

Because step 6 reads step 5 reads step 4 ... reads step 1, an error in any step
makes every later step wrong too — the chain **cascades**.

## Notes

* Deterministic, stdlib only. Float maps compared with tolerance (`gu.close`),
  never `==`. Integer counts and string ids/tokens compared exactly.
* Step 1's `--in` is `data/docs.json`; each later step's `--in` is the previous
  step's `--out`.
