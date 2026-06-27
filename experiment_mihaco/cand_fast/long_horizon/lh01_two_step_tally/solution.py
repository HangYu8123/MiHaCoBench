import argparse
import hashlib
import itertools
import json


def main():
    parser = argparse.ArgumentParser(description="Two-step tally pipeline")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    # Read raw bytes first for provenance, then parse JSON
    raw_bytes = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    payload = json.loads(raw_bytes)

    if args.step == 1:
        values = payload["values"]
        data = [v * 2 + 1 for v in values]
        result = {"step": 1, "data": data, "provenance": provenance}

    elif args.step == 2:
        data = payload["data"]
        cumsum = list(itertools.accumulate(data))
        total = sum(data)
        mean = total / len(data)
        count = len(data)
        result = {
            "step": 2,
            "data": {"cumsum": cumsum, "total": total, "mean": mean, "count": count},
            "provenance": provenance,
        }

    else:
        raise ValueError(f"Unknown step: {args.step}")

    with open(args.out_path, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
