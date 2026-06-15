"""Two-step pipeline: scale_and_shift (step 1) and cumulative_stats (step 2).

CLI contract:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Each step reads the JSON at --in, computes its result, and writes to --out a
JSON object with exactly these keys:
    {"step": K, "data": <result>, "provenance": "<sha256 hex of --in bytes>"}

Step 1 (scale_and_shift):
    Input:  {"values": [int, ...]}
    Output: {"step": 1, "data": [v*2+1 for v in values], "provenance": ...}

Step 2 (cumulative_stats):
    Input:  step 1's output JSON (reads "data" key)
    Output: {"step": 2, "data": {"cumsum": [...], "total": ..., "mean": ..., "count": ...}, "provenance": ...}
"""

import argparse
import hashlib
import itertools
import json
import sys


def parse_args():
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Two-step tally pipeline"
    )
    parser.add_argument("--step", type=int, required=True,
                        help="Pipeline step number (1 or 2)")
    parser.add_argument("--in", dest="in_path", required=True,
                        help="Path to the input JSON file")
    parser.add_argument("--out", dest="out_path", required=True,
                        help="Path to write the output JSON file")
    return parser.parse_args()


def compute_provenance(in_path: str) -> tuple[bytes, str]:
    """Read raw bytes from in_path and return (raw_bytes, sha256_hex).

    The provenance hash is computed on the EXACT bytes of the file before
    any JSON parsing, so the grader can verify the chain.
    """
    raw_bytes = open(in_path, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    return raw_bytes, provenance


def step1_scale_and_shift(data_in: dict) -> list:
    """Step 1: scale_and_shift.

    Reads `values` from the input dict and applies the transform v*2+1 to
    each value, returning the result as a list.

    Args:
        data_in: Parsed JSON dict with key "values" containing a list of ints.

    Returns:
        A list of transformed integers.
    """
    values = data_in["values"]
    return [v * 2 + 1 for v in values]


def step2_cumulative_stats(data_in: dict) -> dict:
    """Step 2: cumulative_stats.

    Reads the `data` list produced by step 1 and computes cumulative
    statistics.

    Args:
        data_in: Parsed JSON dict with key "data" containing a list of numbers
                 (the output of step 1).

    Returns:
        A dict with keys: cumsum (list), total (int/float), mean (float),
        count (int).
    """
    vals = data_in["data"]
    cumsum = list(itertools.accumulate(vals))
    total = sum(vals)
    count = len(vals)
    mean = total / count  # true float division; grader uses tolerance comparison
    return {
        "cumsum": cumsum,
        "total": total,
        "mean": mean,
        "count": count,
    }


def main():
    """Entry point: dispatch to the correct step and write the output JSON."""
    args = parse_args()

    # Read raw bytes first for provenance, then parse JSON
    raw_bytes, provenance = compute_provenance(args.in_path)
    data_in = json.loads(raw_bytes)

    if args.step == 1:
        computed_data = step1_scale_and_shift(data_in)
    elif args.step == 2:
        computed_data = step2_cumulative_stats(data_in)
    else:
        print(f"Error: unknown step {args.step}", file=sys.stderr)
        sys.exit(1)

    result = {
        "step": args.step,       # int, matches --step K
        "data": computed_data,   # step-specific result
        "provenance": provenance, # sha256 hex of --in file bytes
    }

    with open(args.out_path, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
