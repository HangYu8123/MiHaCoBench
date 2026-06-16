"""
16-step token pipeline. Each step reads the prior step's artifact, computes
its result, and writes a new artifact with exactly these keys:
  {"step": K, "data": <result>, "provenance": "<sha256 hex>"}
"""

import argparse
import hashlib
import itertools
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    # Compute provenance from raw bytes BEFORE JSON parsing
    raw = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw).hexdigest()

    prev = json.loads(raw)
    step = args.step

    if step == 1:
        # Step 1 reads prev["values"] (raw input list)
        values = prev["values"]
        data = [float(x) for x in values]

    else:
        # Steps 2-16 read prev["data"]
        data = prev["data"]

        if step == 2:
            # add_const: add 1 to every element
            data = [x + 1.0 for x in data]

        elif step == 3:
            # double: multiply every element by 2
            data = [x * 2.0 for x in data]

        elif step == 4:
            # mod: apply % 5 (Python modulo) to every element
            data = [x % 5 for x in data]

        elif step == 5:
            # scale_by_index: multiply each element by its zero-based index
            data = [data[i] * i for i in range(len(data))]

        elif step == 6:
            # cumsum: replace list with cumulative sums (running totals)
            result = []
            running = 0.0
            for x in data:
                running += x
                result.append(running)
            data = result

        elif step == 7:
            # prefix_max: replace list with running prefix maximum
            result = []
            running_max = data[0]
            for x in data:
                if x > running_max:
                    running_max = x
                result.append(running_max)
            data = result

        elif step == 8:
            # diffs: consecutive differences, output length = input length - 1
            data = [data[i + 1] - data[i] for i in range(len(data) - 1)]

        elif step == 9:
            # abs: apply abs() to every element
            data = [abs(x) for x in data]

        elif step == 10:
            # square: square every element
            data = [x * x for x in data]

        elif step == 11:
            # normalize_minmax: (x - min) / (max - min); all zeros if all equal
            mn = min(data)
            mx = max(data)
            denom = mx - mn
            if denom == 0:
                data = [0.0 for _ in data]
            else:
                data = [(x - mn) / denom for x in data]

        elif step == 12:
            # scale: multiply every element by 10
            data = [x * 10.0 for x in data]

        elif step == 13:
            # round3: round every element to 3 decimal places (Python built-in round)
            data = [round(x, 3) for x in data]

        elif step == 14:
            # sort_asc: sort the list ascending
            data = sorted(data)

        elif step == 15:
            # dedupe: remove consecutive duplicate values (like itertools.groupby)
            data = [k for k, _ in itertools.groupby(data)]

        elif step == 16:
            # aggregate: produce summary dict over the deduplicated list
            s = float(sum(data))
            count = int(len(data))
            mean = float(s / count)
            mx = float(max(data))
            mn = float(min(data))
            data = {"sum": s, "mean": mean, "max": mx, "min": mn, "count": count}

        else:
            raise ValueError(f"Unknown step: {step}")

    output = {"step": step, "data": data, "provenance": provenance}
    with open(args.out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
