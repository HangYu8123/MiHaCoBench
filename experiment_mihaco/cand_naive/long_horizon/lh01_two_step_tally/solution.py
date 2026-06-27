import argparse
import hashlib
import json


def compute_provenance(in_path: str) -> str:
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1(in_path: str) -> dict:
    with open(in_path, "r") as f:
        data = json.load(f)
    values = data["values"]
    result = [v * 2 + 1 for v in values]
    return result


def step2(in_path: str) -> dict:
    with open(in_path, "r") as f:
        data = json.load(f)
    values = data["data"]
    cumsum = []
    running = 0
    for v in values:
        running += v
        cumsum.append(running)
    total = sum(values)
    mean = total / len(values) if values else 0.0
    count = len(values)
    return {"cumsum": cumsum, "total": total, "mean": mean, "count": count}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    provenance = compute_provenance(args.in_path)

    if args.step == 1:
        result = step1(args.in_path)
    elif args.step == 2:
        result = step2(args.in_path)
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
