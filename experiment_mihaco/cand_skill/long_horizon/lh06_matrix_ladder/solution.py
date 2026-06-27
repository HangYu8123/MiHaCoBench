"""
matrix_ladder — 12-step sequential pipeline.
CLI: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
Output JSON: {"step": K, "data": <result>, "provenance": "<sha256hex>"}
"""

import argparse
import hashlib
import itertools
import json
import sys


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def read_input(in_path):
    """Return (raw_bytes, parsed_json) — bytes captured before any parsing."""
    raw = open(in_path, 'rb').read()
    return raw, json.loads(raw)


def write_output(out_path, step, data, provenance):
    """Write deterministic compact JSON."""
    obj = {"step": step, "data": data, "provenance": provenance}
    text = json.dumps(obj, separators=(',', ':'))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def step_1(raw_obj):
    """parse: convert each integer in values to float."""
    return [float(x) for x in raw_obj["values"]]


def step_2(raw_obj):
    """add_const: add 5.0 to every element."""
    data = raw_obj["data"]
    return [x + 5.0 for x in data]


def step_3(raw_obj):
    """mod: apply % 7 to every element (Python float %)."""
    data = raw_obj["data"]
    return [x % 7 for x in data]


def step_4(raw_obj):
    """scale_by_index: multiply element at position i by i (0-based)."""
    data = raw_obj["data"]
    return [i * x for i, x in enumerate(data)]


def step_5(raw_obj):
    """cumsum: running cumulative sum left-to-right."""
    data = raw_obj["data"]
    return list(itertools.accumulate(data))


def step_6(raw_obj):
    """prefix_max: running maximum left-to-right."""
    data = raw_obj["data"]
    return list(itertools.accumulate(data, max))


def step_7(raw_obj):
    """diffs: consecutive differences data[i+1] - data[i], length n-1."""
    data = raw_obj["data"]
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_8(raw_obj):
    """abs: absolute value of every element."""
    data = raw_obj["data"]
    return [abs(x) for x in data]


def step_9(raw_obj):
    """filter_gt_mean: keep only elements strictly greater than the mean."""
    data = raw_obj["data"]
    # Compute mean FIRST on the full list, then filter — order matters.
    m = sum(data) / len(data)
    return [x for x in data if x > m]


def step_10(raw_obj):
    """sort_asc: sort elements ascending."""
    data = raw_obj["data"]
    return sorted(data)


def step_11(raw_obj):
    """dedupe: remove duplicate values, preserving order of first occurrence."""
    data = raw_obj["data"]
    return list(dict.fromkeys(data))


def step_12(raw_obj):
    """aggregate: compute summary statistics."""
    data = raw_obj["data"]
    n = len(data)
    total = sum(data)
    return {
        "total": float(total),
        "mean": float(total / n),
        "count": int(n),
        "min": float(min(data)),
        "max": float(max(data)),
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

STEPS = {
    1: step_1,
    2: step_2,
    3: step_3,
    4: step_4,
    5: step_5,
    6: step_6,
    7: step_7,
    8: step_8,
    9: step_9,
    10: step_10,
    11: step_11,
    12: step_12,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="matrix_ladder pipeline step")
    parser.add_argument('--step', type=int, required=True, help="Step number (1-12)")
    parser.add_argument('--in', dest='in_path', required=True, help="Path to input JSON file")
    parser.add_argument('--out', dest='out_path', required=True, help="Path to output JSON file")
    args = parser.parse_args()

    if args.step not in STEPS:
        print(f"Error: step {args.step} is not in range 1–12", file=sys.stderr)
        sys.exit(1)

    # Read raw bytes first (for provenance), then parse JSON.
    raw_bytes, parsed = read_input(args.in_path)

    # Compute provenance hash from the exact bytes of the --in file.
    provenance = hashlib.sha256(raw_bytes).hexdigest()

    # Execute step.
    result = STEPS[args.step](parsed)

    # Write output.
    write_output(args.out_path, args.step, result, provenance)


if __name__ == '__main__':
    main()
