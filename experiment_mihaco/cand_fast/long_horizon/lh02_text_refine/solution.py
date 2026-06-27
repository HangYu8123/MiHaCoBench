import argparse
import collections
import hashlib
import json
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--in', dest='in_path', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    # Read raw bytes for provenance before JSON parsing
    raw_bytes = open(args.in_path, 'rb').read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()

    prev = json.loads(raw_bytes)

    if args.step == 1:
        # normalize: lowercase then replace non-letter non-space with single space
        s = prev["text"].lower()
        result = re.sub(r'[^a-z ]', ' ', s)

    elif args.step == 2:
        # tokenize: split on whitespace, drop empty tokens
        result = prev["data"].split()

    elif args.step == 3:
        # count: occurrences of each token
        result = dict(collections.Counter(prev["data"]))

    elif args.step == 4:
        # top_k: top 3 by count descending, ties broken alphabetically ascending
        items = sorted(prev["data"].items(), key=lambda x: (-x[1], x[0]))[:3]
        result = [list(pair) for pair in items]

    else:
        raise ValueError(f"Unknown step: {args.step}")

    output = {"step": args.step, "data": result, "provenance": provenance}
    with open(args.out, 'w') as f:
        json.dump(output, f)


if __name__ == '__main__':
    main()
