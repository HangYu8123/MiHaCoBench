"""lh04_ledger_roll — 8-step ledger pipeline."""

import argparse
import hashlib
import json


def compute_provenance(in_path: str) -> str:
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_output(out_path: str, step: int, data, provenance: str) -> None:
    with open(out_path, "w") as f:
        json.dump({"step": step, "data": data, "provenance": provenance}, f)


def step_1(in_path: str, out_path: str) -> None:
    """Parse: cast values to float."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    result = [float(x) for x in obj["values"]]
    write_output(out_path, 1, result, provenance)


def step_2(in_path: str, out_path: str) -> None:
    """Cumsum: running cumulative sum."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    data = obj["data"]
    total = 0.0
    result = []
    for x in data:
        total += x
        result.append(total)
    write_output(out_path, 2, result, provenance)


def step_3(in_path: str, out_path: str) -> None:
    """Prefix_min: running minimum (min seen so far at each index)."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    data = obj["data"]
    cur_min = float("inf")
    result = []
    for x in data:
        cur_min = min(cur_min, x)
        result.append(cur_min)
    write_output(out_path, 3, result, provenance)


def step_4(in_path: str, out_path: str) -> None:
    """Diffs: consecutive differences, output length = N-1."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    data = obj["data"]
    result = [data[i + 1] - data[i] for i in range(len(data) - 1)]
    write_output(out_path, 4, result, provenance)


def step_5(in_path: str, out_path: str) -> None:
    """Abs: element-wise absolute value."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    data = obj["data"]
    result = [abs(x) for x in data]
    write_output(out_path, 5, result, provenance)


def step_6(in_path: str, out_path: str) -> None:
    """Sort_asc: sort ascending."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    data = obj["data"]
    result = sorted(data)
    write_output(out_path, 6, result, provenance)


def step_7(in_path: str, out_path: str) -> None:
    """Dedupe: remove duplicates preserving first-occurrence order."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    data = obj["data"]
    seen = set()
    result = []
    for x in data:
        if x not in seen:
            seen.add(x)
            result.append(x)
    write_output(out_path, 7, result, provenance)


def step_8(in_path: str, out_path: str) -> None:
    """Aggregate: compute sum, mean, count, min, max."""
    provenance = compute_provenance(in_path)
    with open(in_path) as f:
        obj = json.load(f)
    data = obj["data"]
    count = int(len(data))
    sum_val = float(sum(data))
    mean_val = float(sum_val / count) if count else 0.0
    result = {
        "sum": sum_val,
        "mean": mean_val,
        "count": count,
        "min": float(min(data)),
        "max": float(max(data)),
    }
    write_output(out_path, 8, result, provenance)


def main() -> None:
    parser = argparse.ArgumentParser(description="lh04_ledger_roll pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-8)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    dispatch = {
        1: step_1,
        2: step_2,
        3: step_3,
        4: step_4,
        5: step_5,
        6: step_6,
        7: step_7,
        8: step_8,
    }

    if args.step not in dispatch:
        raise ValueError(f"Unknown step: {args.step}. Must be 1-8.")

    dispatch[args.step](args.in_path, args.out)


if __name__ == "__main__":
    main()
