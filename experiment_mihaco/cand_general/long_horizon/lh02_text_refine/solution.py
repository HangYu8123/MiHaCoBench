import argparse
import hashlib
import json
import re
import collections


def main():
    parser = argparse.ArgumentParser(description="Text refinement pipeline")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Read raw bytes first for provenance, then parse JSON
    raw = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw).hexdigest()
    prev = json.loads(raw)

    step = args.step

    if step == 1:
        # normalize: lowercase then replace non-letter/non-space chars with single space
        text = prev["text"]
        lowered = text.lower()
        data = re.sub(r"[^a-z ]", " ", lowered)
        # No stripping, no collapsing of consecutive spaces

    elif step == 2:
        # tokenize: split on whitespace, drop empty tokens
        data = prev["data"].split()

    elif step == 3:
        # count: count occurrences of each unique token
        data = dict(collections.Counter(prev["data"]))

    elif step == 4:
        # top_k: top 3 entries by count descending, tie-break by word ascending
        items = sorted(prev["data"].items(), key=lambda x: (-x[1], x[0]))
        data = [[w, c] for w, c in items[:3]]

    else:
        raise ValueError(f"Unknown step: {step}")

    result = {"step": step, "data": data, "provenance": provenance}

    with open(args.out, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
