"""
Long-Horizon 02 — text_refine
4-step text-processing pipeline.
"""

import argparse
import hashlib
import json
import re


def compute_provenance(in_path: str) -> str:
    """Compute sha256 hex digest of the exact bytes of the input file."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_normalize(prev: dict) -> str:
    """
    Lowercase the text, then replace every character that is NOT an ASCII
    letter or a space with a single space.
    """
    text = prev["text"]
    text = text.lower()
    # Replace non-(ASCII letter or space) characters with a single space
    text = re.sub(r"[^a-z ]", " ", text)
    return text


def step2_tokenize(prev: dict) -> list:
    """
    Split the normalized string on whitespace and drop empty tokens.
    """
    normalized = prev["data"]
    tokens = [t for t in normalized.split() if t]
    return tokens


def step3_count(prev: dict) -> dict:
    """
    Count occurrences of each unique token.
    """
    tokens = prev["data"]
    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def step4_top_k(prev: dict) -> list:
    """
    Return top 3 entries by count descending; break ties by word ascending.
    """
    counts = prev["data"]
    k = 3
    # Sort: primary key = count descending (-count), secondary key = word ascending
    sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    top = sorted_items[:k]
    return [[word, count] for word, count in top]


STEP_FUNCTIONS = {
    1: step1_normalize,
    2: step2_tokenize,
    3: step3_count,
    4: step4_top_k,
}


def main():
    parser = argparse.ArgumentParser(description="Text Refine Pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-4)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step not in STEP_FUNCTIONS:
        raise ValueError(f"Invalid step: {step}. Must be 1, 2, 3, or 4.")

    # Read input
    with open(in_path, "r", encoding="utf-8") as f:
        prev = json.load(f)

    # Compute provenance (sha256 of the exact bytes of the input file)
    provenance = compute_provenance(in_path)

    # Run the appropriate step
    result = STEP_FUNCTIONS[step](prev)

    # Write output
    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
