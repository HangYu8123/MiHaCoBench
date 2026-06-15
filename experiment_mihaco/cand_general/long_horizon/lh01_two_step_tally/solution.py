"""Two-step tally pipeline.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>

Step 1 (scale_and_shift):
    Reads {"values": [...]} from --in.
    Produces data = [v * 2 + 1 for v in values].

Step 2 (cumulative_stats):
    Reads step 1's artifact {"step": 1, "data": [...], "provenance": "..."}.
    Produces {"cumsum": [...], "total": <int>, "mean": <float>, "count": <int>}.

Every step writes:
    {"step": K, "data": <result>, "provenance": "<sha256 hex of --in file bytes>"}
"""

import argparse
import hashlib
import json


def step1(in_data: dict) -> list:
    """Scale and shift: apply v * 2 + 1 to each element of in_data['values'].

    Args:
        in_data: Parsed JSON object expected to contain key 'values' whose
                 value is a list of numbers.

    Returns:
        A list of numbers with the transformation applied.

    Raises:
        KeyError: If 'values' is missing from in_data.
        TypeError: If in_data['values'] is not iterable.
    """
    values = in_data["values"]
    return [v * 2 + 1 for v in values]


def step2(in_data: dict) -> dict:
    """Cumulative stats: compute running cumulative sums, total, mean, and count.

    Reads the 'data' key from in_data (step 1's artifact).

    Args:
        in_data: Parsed JSON artifact from step 1, expected to contain key
                 'data' whose value is a list of numbers.

    Returns:
        A dict with keys:
            'cumsum' (list of running cumulative sums),
            'total'  (sum of all values; int if all inputs are int, else float),
            'mean'   (float; total / count),
            'count'  (int; number of elements).

    Raises:
        KeyError: If 'data' is missing from in_data.
        ZeroDivisionError: If 'data' is an empty list (mean is undefined).
    """
    lst = in_data["data"]
    count = len(lst)
    if count == 0:
        raise ZeroDivisionError(
            "Step 2 received an empty list; mean is undefined for an empty sequence."
        )

    running = 0
    cumsum = []
    for v in lst:
        running += v
        cumsum.append(running)
    total = running
    mean = total / count  # True division — always produces float in Python 3.

    return {
        "cumsum": cumsum,
        "total": total,
        "mean": mean,
        "count": count,
    }


def main() -> None:
    """Parse CLI arguments, dispatch to the appropriate step, and write output."""
    parser = argparse.ArgumentParser(
        description="Two-step tally pipeline — run one step per invocation."
    )
    parser.add_argument(
        "--step",
        type=int,
        required=True,
        help="Pipeline step to execute (1 or 2).",
    )
    # '--in' is a valid argparse flag string; we use dest='in_path' because
    # 'in' is a Python reserved keyword and cannot be used as an attribute name.
    parser.add_argument(
        "--in",
        dest="in_path",
        required=True,
        help="Path to the input JSON file.",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        required=True,
        help="Path to write the output JSON file.",
    )
    args = parser.parse_args()

    step = args.step
    in_path = args.in_path
    out_path = args.out_path

    # Read input once in binary mode:
    #   - 'rb' avoids platform line-ending translation that would corrupt the hash.
    #   - json.loads() accepts bytes directly on Python 3.6+.
    with open(in_path, "rb") as fh:
        bytes_in = fh.read()

    # Compute provenance BEFORE parsing so it covers the exact on-disk bytes.
    provenance = hashlib.sha256(bytes_in).hexdigest()

    in_data = json.loads(bytes_in)

    if step == 1:
        result = step1(in_data)
    elif step == 2:
        result = step2(in_data)
    else:
        raise ValueError(
            f"Unknown step {step!r}. Only steps 1 and 2 are supported."
        )

    out_obj = {"step": step, "data": result, "provenance": provenance}

    # Write as UTF-8 text; json.dumps returns str, so 'w' mode is correct.
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out_obj))


if __name__ == "__main__":
    main()
