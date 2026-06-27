import argparse
import hashlib
import itertools
import json
import sys


def step_1(payload):
    """scale_and_shift: read values; produce [v * 2 + 1 for v in values]."""
    values = payload["values"]
    return [v * 2 + 1 for v in values]


def step_2(payload):
    """cumulative_stats: read list from step 1 data; produce stats dict."""
    values = payload["data"]
    cumsum = list(itertools.accumulate(values))
    total = sum(values)
    count = len(values)
    mean = float(total) / count
    return {"cumsum": cumsum, "total": total, "mean": mean, "count": count}


def main():
    parser = argparse.ArgumentParser(description="Two-step tally pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1 or 2)")
    parser.add_argument("--in", dest="input_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="output_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    in_path = args.input_path
    out_path = args.output_path
    step_k = args.step

    # Read raw bytes BEFORE any JSON parse — provenance hashes exact file bytes
    raw = open(in_path, "rb").read()
    provenance = hashlib.sha256(raw).hexdigest()
    payload = json.loads(raw)

    if step_k == 1:
        result = step_1(payload)
    elif step_k == 2:
        result = step_2(payload)
    else:
        print(f"Unknown step: {step_k}", file=sys.stderr)
        sys.exit(1)

    output = {"step": step_k, "data": result, "provenance": provenance}
    with open(out_path, "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    # Self-tests (TDD — run inline before main execution if --test flag present)
    # Verify step_1
    assert step_1({"values": [5, 3, 8, 1, 9, 2, 7]}) == [11, 7, 17, 3, 19, 5, 15], "step_1 failed"

    # Verify step_2
    s2_result = step_2({"data": [11, 7, 17, 3, 19, 5, 15]})
    assert s2_result["cumsum"] == [11, 18, 35, 38, 57, 62, 77], f"cumsum failed: {s2_result['cumsum']}"
    assert s2_result["total"] == 77, f"total failed: {s2_result['total']}"
    assert s2_result["mean"] == 11.0, f"mean failed: {s2_result['mean']}"
    assert isinstance(s2_result["mean"], float), f"mean is not float: {type(s2_result['mean'])}"
    assert s2_result["count"] == 7, f"count failed: {s2_result['count']}"
    assert isinstance(s2_result["cumsum"], list), f"cumsum is not list: {type(s2_result['cumsum'])}"

    main()
