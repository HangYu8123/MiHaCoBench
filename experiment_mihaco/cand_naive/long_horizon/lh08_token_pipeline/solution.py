"""
token_pipeline — 16-step pipeline solution.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def run_step(step: int, in_path: str, out_path: str) -> None:
    # Read raw bytes first for provenance
    raw_bytes = open(in_path, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse JSON
    prev = json.loads(raw_bytes)

    # Extract input data
    if step == 1:
        data = prev["values"]
    else:
        data = prev["data"]

    # Apply the operation for this step
    if step == 1:
        # parse: cast each integer to float
        result = [float(x) for x in data]

    elif step == 2:
        # add_const: add 1 to every element
        result = [x + 1.0 for x in data]

    elif step == 3:
        # double: multiply every element by 2
        result = [x * 2.0 for x in data]

    elif step == 4:
        # mod: apply % 5 (Python modulo) to every element
        result = [x % 5.0 for x in data]

    elif step == 5:
        # scale_by_index: multiply each element by its zero-based index
        result = [x * float(i) for i, x in enumerate(data)]

    elif step == 6:
        # cumsum: replace list with cumulative sums
        result = []
        running = 0.0
        for x in data:
            running += x
            result.append(running)

    elif step == 7:
        # prefix_max: replace list with running prefix maximum
        result = []
        current_max = None
        for x in data:
            if current_max is None or x > current_max:
                current_max = x
            result.append(current_max)

    elif step == 8:
        # diffs: consecutive differences, length decreases by 1
        result = [data[i + 1] - data[i] for i in range(len(data) - 1)]

    elif step == 9:
        # abs: apply abs() to every element
        result = [abs(x) for x in data]

    elif step == 10:
        # square: square every element
        result = [x * x for x in data]

    elif step == 11:
        # normalize_minmax: (x - min) / (max - min), or all zeros if all equal
        mn = min(data)
        mx = max(data)
        if mx == mn:
            result = [0.0 for _ in data]
        else:
            result = [(x - mn) / (mx - mn) for x in data]

    elif step == 12:
        # scale: multiply every element by 10
        result = [x * 10.0 for x in data]

    elif step == 13:
        # round3: round every element to 3 decimal places
        result = [round(x, 3) for x in data]

    elif step == 14:
        # sort_asc: sort the list ascending
        result = sorted(data)

    elif step == 15:
        # dedupe: remove consecutive duplicate values (keep first)
        result = []
        prev_val = object()  # sentinel
        for x in data:
            if x != prev_val:
                result.append(x)
                prev_val = x

    elif step == 16:
        # aggregate: produce summary dict
        total = sum(data)
        count = len(data)
        mean = total / count if count > 0 else 0.0
        result = {
            "sum": float(total),
            "mean": float(mean),
            "max": float(max(data)),
            "min": float(min(data)),
            "count": int(count),
        }

    else:
        raise ValueError(f"Unknown step: {step}")

    # Write output
    output = {"step": step, "data": result, "provenance": provenance}
    with open(out_path, "w") as f:
        json.dump(output, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    run_step(args.step, args.in_path, args.out_path)


if __name__ == "__main__":
    main()
