"""Deliberately-broken reference for long_horizon/lh02_text_refine.

Planted defect: step 4 sorts entries by count **ascending** instead of
descending, producing the wrong top-k order. Steps 1-3 are correct.

This must fail test_step[4] and test_final_cumulative.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re


def step1_normalize(prev: dict) -> str:
    """Lowercase and replace every non-letter/non-space char with a space."""
    text = prev["text"].lower()
    return re.sub(r"[^a-z ]", " ", text)


def step2_tokenize(prev: dict) -> list:
    """Split the normalized string on whitespace, dropping empty tokens."""
    return prev["data"].split()


def step3_count(prev: dict) -> dict:
    """Count occurrences of each token."""
    counts: dict[str, int] = {}
    for word in prev["data"]:
        counts[word] = counts.get(word, 0) + 1
    return counts


def step4_top_k(prev: dict, k: int = 3) -> list:
    """BUG: sorts by count ascending instead of descending."""
    items = sorted(prev["data"].items(), key=lambda x: (x[1], x[0]))  # BUG: ascending count
    return [[word, count] for word, count in items[:k]]


STEPS = {
    1: step1_normalize,
    2: step2_tokenize,
    3: step3_count,
    4: step4_top_k,
}


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = STEPS[args.step](prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
