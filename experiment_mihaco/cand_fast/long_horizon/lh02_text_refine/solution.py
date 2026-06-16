import argparse
import hashlib
import json
import re
import collections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    # Compute provenance from raw bytes of input file before any parsing
    raw_bytes = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse the input JSON
    prev = json.loads(raw_bytes)

    if args.step == 1:
        # Step 1 — normalize: read prev["text"], lowercase, replace non-letter/non-space with space
        text = prev["text"].lower()
        result = re.sub(r"[^a-z ]", " ", text)

    elif args.step == 2:
        # Step 2 — tokenize: split on whitespace, drop empty tokens
        result = prev["data"].split()

    elif args.step == 3:
        # Step 3 — count: count occurrences of each token
        counter = collections.Counter(prev["data"])
        result = dict(counter)

    elif args.step == 4:
        # Step 4 — top_k: top 3 entries by count desc, ties broken by word asc
        counts = prev["data"]
        sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:3]
        result = [[word, count] for word, count in sorted_items]

    else:
        raise ValueError(f"Unknown step: {args.step}")

    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
