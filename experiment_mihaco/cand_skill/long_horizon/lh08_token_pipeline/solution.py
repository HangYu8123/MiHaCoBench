"""
lh08_token_pipeline — 16-step processing pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Each step reads the JSON at --in, computes its result, and writes to --out:
    {"step": K, "data": <result>, "provenance": "<sha256 hex of raw --in bytes>"}
"""

import argparse
import hashlib
import json
import sys


def step1_parse(prev):
    """Cast each integer in 'values' to float."""
    return [float(x) for x in prev["values"]]


def step2_add_const(prev):
    """Add 1 to every element."""
    d = prev["data"]
    return [x + 1.0 for x in d]


def step3_double(prev):
    """Multiply every element by 2."""
    d = prev["data"]
    return [x * 2.0 for x in d]


def step4_mod(prev):
    """Apply % 5 (Python modulo) to every element."""
    d = prev["data"]
    return [x % 5 for x in d]


def step5_scale_by_index(prev):
    """Multiply each element by its zero-based index."""
    d = prev["data"]
    return [d[i] * i for i in range(len(d))]


def step6_cumsum(prev):
    """Replace list with cumulative sums (running totals)."""
    d = prev["data"]
    result = []
    acc = 0.0
    for x in d:
        acc += x
        result.append(acc)
    return result


def step7_prefix_max(prev):
    """Replace list with running prefix maximum."""
    d = prev["data"]
    result = []
    mx = d[0]
    for x in d:
        if x > mx:
            mx = x
        result.append(mx)
    return result


def step8_diffs(prev):
    """Replace list with consecutive differences. Length decreases by 1."""
    d = prev["data"]
    return [d[i + 1] - d[i] for i in range(len(d) - 1)]


def step9_abs(prev):
    """Apply abs() to every element."""
    d = prev["data"]
    return [abs(x) for x in d]


def step10_square(prev):
    """Square every element (x * x)."""
    d = prev["data"]
    return [x * x for x in d]


def step11_normalize_minmax(prev):
    """Apply min-max normalisation. If all values equal, produce all zeros."""
    d = prev["data"]
    mn = min(d)
    mx = max(d)
    if mx == mn:
        return [0.0 for _ in d]
    return [(x - mn) / (mx - mn) for x in d]


def step12_scale(prev):
    """Multiply every element by 10."""
    d = prev["data"]
    return [x * 10.0 for x in d]


def step13_round3(prev):
    """Round every element to 3 decimal places."""
    d = prev["data"]
    return [round(x, 3) for x in d]


def step14_sort_asc(prev):
    """Sort the list ascending."""
    d = prev["data"]
    return sorted(d)


def step15_dedupe(prev):
    """Remove consecutive duplicate values (preserve order, keep first)."""
    d = prev["data"]
    if not d:
        return []
    result = [d[0]]
    for x in d[1:]:
        if x != result[-1]:
            result.append(x)
    return result


def step16_aggregate(prev):
    """Produce a summary dict over the deduplicated list."""
    d = prev["data"]
    n = len(d)
    total = sum(d)
    return {
        "sum": total,
        "mean": total / n,
        "max": max(d),
        "min": min(d),
        "count": n,
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
    parser = argparse.ArgumentParser(description="16-step token pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-16)")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file path")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Read raw bytes FIRST for provenance (before JSON parsing)
    with open(args.input, "rb") as f:
        raw_bytes = f.read()

    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Parse JSON from raw bytes
    prev = json.loads(raw_bytes.decode("utf-8"))

    step_k = args.step
    if step_k not in STEP_FUNCS:
        print(f"Error: step {step_k} is not defined (must be 1-16)", file=sys.stderr)
        sys.exit(1)

    result = STEP_FUNCS[step_k](prev)

    output = {
        "step": step_k,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
