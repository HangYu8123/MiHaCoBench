"""
lh02_text_refine — 4-step text-processing pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import collections
import hashlib
import json
import re
import sys


def normalize(text: str) -> str:
    """Step 1: lowercase then replace every non-letter/non-space char with a single space."""
    s = text.lower()
    s = re.sub(r'[^a-z ]', ' ', s)
    return s


def tokenize(text: str) -> list:
    """Step 2: split on whitespace, drop empty tokens."""
    return text.split()


def count_tokens(tokens: list) -> dict:
    """Step 3: count occurrences of each unique token."""
    return dict(collections.Counter(tokens))


def top_k(counts: dict, k: int = 3) -> list:
    """Step 4: return top-k entries by count desc, ties broken alphabetically asc."""
    sorted_pairs = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [[w, c] for w, c in sorted_pairs[:k]]


def main():
    parser = argparse.ArgumentParser(description="4-step text-processing pipeline")
    parser.add_argument('--step', type=int, required=True, help='Step number (1-4)')
    parser.add_argument('--in', dest='in_path', required=True, help='Input JSON file path')
    parser.add_argument('--out', dest='out_path', required=True, help='Output JSON file path')
    args = parser.parse_args()

    # Read input file bytes for provenance hash
    with open(args.in_path, 'rb') as f:
        in_bytes = f.read()

    provenance = hashlib.sha256(in_bytes).hexdigest()

    # Parse input JSON
    prev = json.loads(in_bytes)

    # Execute the requested step
    step = args.step
    if step == 1:
        result = normalize(prev["text"])
    elif step == 2:
        result = tokenize(prev["data"])
    elif step == 3:
        result = count_tokens(prev["data"])
    elif step == 4:
        result = top_k(prev["data"])
    else:
        print(f"Error: unknown step {step}", file=sys.stderr)
        sys.exit(1)

    # Build output object (insertion-ordered: step, data, provenance)
    output = {"step": step, "data": result, "provenance": provenance}

    # Write output JSON with a single trailing newline
    out_str = json.dumps(output) + "\n"
    with open(args.out_path, 'w', encoding='utf-8') as f:
        f.write(out_str)


if __name__ == '__main__':
    main()
