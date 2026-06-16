import argparse
import hashlib
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    # Read raw bytes first, then compute provenance
    with open(args.in_path, "rb") as f:
        raw_bytes = f.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse JSON from the same raw bytes
    in_data = json.loads(raw_bytes)

    step = args.step

    if step == 1:
        # parse: read "values" key, convert each to float
        values = in_data["values"]
        result = [float(x) for x in values]
    else:
        # steps 2-12: read "data" key
        data = in_data["data"]

        if step == 2:
            # add_const: add 5.0 to every element
            result = [x + 5.0 for x in data]

        elif step == 3:
            # mod: apply % 7 to every element (Python float %)
            result = [x % 7 for x in data]

        elif step == 4:
            # scale_by_index: multiply element at position i by i (0-based)
            result = [float(i) * x for i, x in enumerate(data)]

        elif step == 5:
            # cumsum: running cumulative sum left-to-right, same length as input
            result = []
            running = 0.0
            for x in data:
                running += x
                result.append(running)

        elif step == 6:
            # prefix_max: running maximum left-to-right, same length as input
            result = []
            running_max = None
            for x in data:
                if running_max is None or x > running_max:
                    running_max = x
                result.append(running_max)

        elif step == 7:
            # diffs: consecutive differences, length n-1
            result = [data[i + 1] - data[i] for i in range(len(data) - 1)]

        elif step == 8:
            # abs: absolute value of every element
            result = [abs(x) for x in data]

        elif step == 9:
            # filter_gt_mean: keep elements strictly greater than mean
            # compute mean over the full list first
            m = sum(data) / len(data)
            result = [x for x in data if x > m]

        elif step == 10:
            # sort_asc: sort elements ascending
            result = sorted(data)

        elif step == 11:
            # dedupe: remove duplicates, preserve first-occurrence order
            seen = set()
            result = []
            for x in data:
                if x not in seen:
                    seen.add(x)
                    result.append(x)

        elif step == 12:
            # aggregate: compute summary statistics
            total = float(sum(data))
            mean = sum(data) / len(data)
            count = int(len(data))
            min_val = float(min(data))
            max_val = float(max(data))
            result = {
                "total": total,
                "mean": mean,
                "count": count,
                "min": min_val,
                "max": max_val,
            }

        else:
            raise ValueError(f"Unknown step: {step}")

    out = {"step": step, "data": result, "provenance": provenance}

    with open(args.out_path, "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    main()
