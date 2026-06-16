import argparse
import hashlib
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="input", required=True)
    parser.add_argument("--out", dest="output", required=True)
    args = parser.parse_args()

    # Read raw bytes for provenance, then parse JSON
    raw_bytes = open(args.input, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    prev = json.loads(raw_bytes)

    step = args.step

    if step == 1:
        # parse: cast values to float
        source = prev["values"]
        result = [float(x) for x in source]

    elif step == 2:
        # double: multiply each element by 2
        source = prev["data"]
        result = [x * 2.0 for x in source]

    elif step == 3:
        # add_const: add 3 to each element
        source = prev["data"]
        result = [x + 3.0 for x in source]

    elif step == 4:
        # filter_gt_mean: keep only elements strictly greater than the mean
        source = prev["data"]
        mean = sum(source) / len(source)
        result = [x for x in source if x > mean]

    elif step == 5:
        # sort_desc: sort in descending order
        source = prev["data"]
        result = sorted(source, reverse=True)

    elif step == 6:
        # aggregate: compute summary statistics
        source = prev["data"]
        total = sum(source)
        count = len(source)
        result = {
            "sum": float(total),
            "mean": float(total / count),
            "min": float(min(source)),
            "max": float(max(source)),
            "count": int(count),
        }

    else:
        raise ValueError(f"Unknown step: {step}")

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.output, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
