import argparse
import hashlib
import json
import re
import collections


def compute_provenance(in_path):
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_normalize(data):
    text = data["text"]
    text = text.lower()
    text = re.sub(r'[^a-z ]', ' ', text)
    return text


def step2_tokenize(data):
    normalized = data["data"]
    tokens = normalized.split()
    return tokens


def step3_count(data):
    tokens = data["data"]
    counter = collections.Counter(tokens)
    return dict(counter)


def step4_top_k(data):
    counts = data["data"]
    # Sort by count descending, then word ascending for ties
    sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    top3 = sorted_items[:3]
    return [[word, count] for word, count in top3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--in', dest='in_path', required=True)
    parser.add_argument('--out', dest='out_path', required=True)
    args = parser.parse_args()

    provenance = compute_provenance(args.in_path)

    with open(args.in_path, 'r', encoding='utf-8') as f:
        prev = json.load(f)

    if args.step == 1:
        result = step1_normalize(prev)
    elif args.step == 2:
        result = step2_tokenize(prev)
    elif args.step == 3:
        result = step3_count(prev)
    elif args.step == 4:
        result = step4_top_k(prev)
    else:
        raise ValueError(f"Unknown step: {args.step}")

    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance
    }

    with open(args.out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f)


if __name__ == '__main__':
    main()
