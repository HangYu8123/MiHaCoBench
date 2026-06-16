"""
Token Pipeline — 16-step sequential processing chain.

CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def step1_parse(prev):
    """Cast each integer in values to float."""
    return [float(x) for x in prev["values"]]


def step2_add_const(prev):
    """Add 1 to every element."""
    return [x + 1.0 for x in prev["data"]]


def step3_double(prev):
    """Multiply every element by 2."""
    return [x * 2.0 for x in prev["data"]]


def step4_mod(prev):
    """Apply % 5 (Python modulo) to every element."""
    return [x % 5 for x in prev["data"]]


def step5_scale_by_index(prev):
    """Multiply each element by its zero-based index."""
    data = prev["data"]
    return [data[i] * i for i in range(len(data))]


def step6_cumsum(prev):
    """Replace list with cumulative sums."""
    data = prev["data"]
    result = []
    total = 0.0
    for x in data:
        total += x
        result.append(total)
    return result


def step7_prefix_max(prev):
    """Replace list with running prefix maximum."""
    data = prev["data"]
    result = []
    current_max = None
    for x in data:
        if current_max is None or x > current_max:
            current_max = x
        result.append(current_max)
    return result


def step8_diffs(prev):
    """Replace list with consecutive differences."""
    data = prev["data"]
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step9_abs(prev):
    """Apply abs() to every element."""
    return [abs(x) for x in prev["data"]]


def step10_square(prev):
    """Square every element."""
    return [x * x for x in prev["data"]]


def step11_normalize_minmax(prev):
    """Apply min-max normalisation."""
    data = prev["data"]
    mn = min(data)
    mx = max(data)
    if mn == mx:
        return [0.0] * len(data)
    rng = mx - mn
    return [(x - mn) / rng for x in data]


def step12_scale(prev):
    """Multiply every element by 10."""
    return [x * 10.0 for x in prev["data"]]


def step13_round3(prev):
    """Round every element to 3 decimal places."""
    return [round(x, 3) for x in prev["data"]]


def step14_sort_asc(prev):
    """Sort the list ascending."""
    return sorted(prev["data"])


def step15_dedupe(prev):
    """Remove consecutive duplicate values."""
    data = prev["data"]
    if not data:
        return []
    result = [data[0]]
    for x in data[1:]:
        if x != result[-1]:
            result.append(x)
    return result


def step16_aggregate(prev):
    """Produce a summary dict."""
    data = prev["data"]
    count = len(data)
    total = sum(data)
    mean = total / count if count > 0 else 0.0
    return {
        "sum": float(total),
        "mean": float(mean),
        "max": float(max(data)),
        "min": float(min(data)),
        "count": int(count),
    }


STEP_FUNCS = {
    1: step1_parse,
    2: step2_add_const,
    3: step3_double,
    4: step4_mod,
    5: step5_scale_by_index,
    6: step6_cumsum,
    7: step7_prefix_max,
    8: step8_diffs,
    9: step9_abs,
    10: step10_square,
    11: step11_normalize_minmax,
    12: step12_scale,
    13: step13_round3,
    14: step14_sort_asc,
    15: step15_dedupe,
    16: step16_aggregate,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Read raw bytes for provenance
    with open(in_path, "rb") as f:
        raw_bytes = f.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse JSON
    prev = json.loads(raw_bytes)

    # Run the step
    if step_num not in STEP_FUNCS:
        print(f"Unknown step: {step_num}", file=sys.stderr)
        sys.exit(1)

    result = STEP_FUNCS[step_num](prev)

    output = {
        "step": step_num,
        "data": result,
        "provenance": provenance,
    }

    with open(out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
