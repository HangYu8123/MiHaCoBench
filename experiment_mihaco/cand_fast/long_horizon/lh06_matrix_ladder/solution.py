"""
Long-Horizon 06 — matrix_ladder (12 steps)
12-step pipeline: each step reads the artifact from the previous step,
computes a result, and writes a JSON artifact with provenance.
"""

import argparse
import hashlib
import itertools
import json


def compute_provenance(in_path: str) -> str:
    """Hash the exact bytes of the input file."""
    with open(in_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def step_parse(d: dict) -> list:
    """Step 1: Convert each integer in 'values' to float."""
    return [float(x) for x in d['values']]


def step_add_const(d: dict) -> list:
    """Step 2: Add 5.0 to every element."""
    data = d['data']
    return [x + 5.0 for x in data]


def step_mod(d: dict) -> list:
    """Step 3: Apply % 7 to every element (Python float %)."""
    data = d['data']
    return [x % 7 for x in data]


def step_scale_by_index(d: dict) -> list:
    """Step 4: Multiply element at position i by i (0-based)."""
    data = d['data']
    return [x * i for i, x in enumerate(data)]


def step_cumsum(d: dict) -> list:
    """Step 5: Running cumulative sum left-to-right."""
    data = d['data']
    return list(itertools.accumulate(data))


def step_prefix_max(d: dict) -> list:
    """Step 6: Running maximum left-to-right."""
    data = d['data']
    return list(itertools.accumulate(data, max))


def step_diffs(d: dict) -> list:
    """Step 7: Consecutive differences: data[i+1] - data[i]. Output length n-1."""
    data = d['data']
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step_abs(d: dict) -> list:
    """Step 8: Absolute value of every element."""
    data = d['data']
    return [abs(x) for x in data]


def step_filter_gt_mean(d: dict) -> list:
    """Step 9: Keep only elements strictly greater than the mean."""
    data = d['data']
    if not data:
        return []
    mean = sum(data) / len(data)
    return [x for x in data if x > mean]


def step_sort_asc(d: dict) -> list:
    """Step 10: Sort elements ascending."""
    data = d['data']
    return sorted(data)


def step_dedupe(d: dict) -> list:
    """Step 11: Remove duplicate values, preserving order of first occurrence."""
    data = d['data']
    seen = set()
    result = []
    for x in data:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def step_aggregate(d: dict) -> dict:
    """Step 12: Compute summary statistics."""
    data = d['data']
    if not data:
        return {
            "total": 0.0,
            "mean": 0.0,
            "count": 0,
            "min": 0.0,
            "max": 0.0,
        }
    total = float(sum(data))
    count = int(len(data))
    mean = float(total / count)
    return {
        "total": total,
        "mean": mean,
        "count": count,
        "min": float(min(data)),
        "max": float(max(data)),
    }


STEPS = {
    1: step_parse,
    2: step_add_const,
    3: step_mod,
    4: step_scale_by_index,
    5: step_cumsum,
    6: step_prefix_max,
    7: step_diffs,
    8: step_abs,
    9: step_filter_gt_mean,
    10: step_sort_asc,
    11: step_dedupe,
    12: step_aggregate,
}


def main():
    parser = argparse.ArgumentParser(description="matrix_ladder 12-step pipeline")
    parser.add_argument('--step', type=int, required=True, help='Step number (1-12)')
    parser.add_argument('--in', dest='in_path', required=True, help='Input JSON path')
    parser.add_argument('--out', required=True, help='Output JSON path')
    args = parser.parse_args()

    # Hash the raw bytes BEFORE parsing (provenance requirement)
    provenance = compute_provenance(args.in_path)

    # Parse input JSON
    with open(args.in_path, 'r') as f:
        d = json.load(f)

    # Execute the requested step
    step_fn = STEPS[args.step]
    result = step_fn(d)

    # Write output
    output = {
        "step": args.step,
        "data": result,
        "provenance": provenance,
    }
    with open(args.out, 'w') as f:
        json.dump(output, f)


if __name__ == '__main__':
    main()
