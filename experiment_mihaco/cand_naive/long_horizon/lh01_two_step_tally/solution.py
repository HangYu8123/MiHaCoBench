"""Two-step tally pipeline.

Step 1 — scale_and_shift:
    Reads {"values": [...]} from --in, produces data = [v * 2 + 1 for v in values].

Step 2 — cumulative_stats:
    Reads step 1's output (data list), produces
    {"cumsum": [...], "total": ..., "mean": ..., "count": ...}.

CLI usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys


def compute_provenance(in_path: str) -> str:
    """Return the SHA-256 hex digest of the exact bytes of the file at in_path."""
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def step1_scale_and_shift(in_path: str) -> list:
    """Read values from input JSON and return [v * 2 + 1 for v in values]."""
    with open(in_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    values = payload["values"]
    return [v * 2 + 1 for v in values]


def step2_cumulative_stats(in_path: str) -> dict:
    """Read step 1's output and compute cumulative stats over its data list."""
    with open(in_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    values = payload["data"]
    count = len(values)
    cumsum = []
    running = 0
    for v in values:
        running += v
        cumsum.append(running)
    total = running
    mean = total / count if count > 0 else 0.0
    return {"cumsum": cumsum, "total": total, "mean": mean, "count": count}


STEPS = {
    1: step1_scale_and_shift,
    2: step2_cumulative_stats,
}


def main():
    """Parse CLI arguments and execute the requested pipeline step."""
    parser = argparse.ArgumentParser(
        description="Two-step tally pipeline.",
    )
    parser.add_argument("--step", type=int, required=True, help="Step number (1 or 2).")
    parser.add_argument("--in", dest="in_path", required=True, help="Path to input JSON.")
    parser.add_argument("--out", dest="out_path", required=True, help="Path for output JSON.")
    args = parser.parse_args()

    step_num = args.step
    in_path = args.in_path
    out_path = args.out_path

    if step_num not in STEPS:
        print(f"Unknown step: {step_num}. Must be one of {list(STEPS.keys())}.", file=sys.stderr)
        sys.exit(1)

    # Compute provenance BEFORE reading content (reads raw bytes once).
    provenance = compute_provenance(in_path)

    # Run the step.
    data = STEPS[step_num](in_path)

    result = {
        "step": step_num,
        "data": data,
        "provenance": provenance,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
