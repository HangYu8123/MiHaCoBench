"""
Long-Horizon 08 — token_pipeline (16 steps)

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import itertools
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Read raw bytes first for provenance, then parse JSON
    raw = open(args.input, "rb").read()
    provenance = hashlib.sha256(raw).hexdigest()
    prev = json.loads(raw)

    step = args.step

    if step == 1:
        # parse: cast each integer in values to float
        values = prev["values"]
        result = [float(x) for x in values]

    elif step == 2:
        # add_const: add 1 to every element
        data = prev["data"]
        result = [x + 1 for x in data]

    elif step == 3:
        # double: multiply every element by 2
        data = prev["data"]
        result = [x * 2 for x in data]

    elif step == 4:
        # mod: apply % 5 (Python modulo) to every element
        data = prev["data"]
        result = [x % 5 for x in data]

    elif step == 5:
        # scale_by_index: multiply each element by its zero-based index
        data = prev["data"]
        result = [data[i] * i for i in range(len(data))]

    elif step == 6:
        # cumsum: replace list with cumulative sums (running totals)
        data = prev["data"]
        acc = 0.0
        result = []
        for x in data:
            acc += x
            result.append(acc)

    elif step == 7:
        # prefix_max: replace list with running prefix maximum
        data = prev["data"]
        mx = data[0]
        result = []
        for x in data:
            mx = max(mx, x)
            result.append(mx)

    elif step == 8:
        # diffs: replace list with consecutive differences
        # output length = input length - 1
        data = prev["data"]
        result = [data[i + 1] - data[i] for i in range(len(data) - 1)]

    elif step == 9:
        # abs: apply abs() to every element
        data = prev["data"]
        result = [abs(x) for x in data]

    elif step == 10:
        # square: square every element (x * x)
        data = prev["data"]
        result = [x * x for x in data]

    elif step == 11:
        # normalize_minmax: apply min-max normalisation
        # if all values equal, produce all zeros
        data = prev["data"]
        mn = min(data)
        mx = max(data)
        if mx == mn:
            result = [0.0 for _ in data]
        else:
            result = [(x - mn) / (mx - mn) for x in data]

    elif step == 12:
        # scale: multiply every element by 10
        data = prev["data"]
        result = [x * 10 for x in data]

    elif step == 13:
        # round3: round every element to 3 decimal places
        data = prev["data"]
        result = [round(x, 3) for x in data]

    elif step == 14:
        # sort_asc: sort the list ascending
        data = prev["data"]
        result = sorted(data)

    elif step == 15:
        # dedupe: remove consecutive duplicate values (preserve order, keep first)
        data = prev["data"]
        result = [k for k, _ in itertools.groupby(data)]

    elif step == 16:
        # aggregate: produce a summary dict
        d = prev["data"]
        total = sum(d)
        count = len(d)
        result = {
            "sum": total,
            "mean": total / count,
            "max": max(d),
            "min": min(d),
            "count": count,  # int, naturally from len()
        }

    else:
        raise ValueError(f"Unknown step: {step}")

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out, "w") as f:
        f.write(json.dumps(output))


if __name__ == "__main__":
    main()
