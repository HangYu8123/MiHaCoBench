import argparse
import hashlib
import json


def step1_parse(data):
    """Cast every element of 'values' to float."""
    return [float(x) for x in data["values"]]


def step2_cumsum(data):
    """Running cumulative sum."""
    result = []
    total = 0.0
    for x in data:
        total += x
        result.append(total)
    return result


def step3_prefix_min(data):
    """Running minimum (min seen so far at each index)."""
    result = []
    cur_min = None
    for x in data:
        if cur_min is None:
            cur_min = x
        else:
            cur_min = min(cur_min, x)
        result.append(cur_min)
    return result


def step4_diffs(data):
    """Consecutive differences: data[i+1] - data[i]."""
    return [data[i + 1] - data[i] for i in range(len(data) - 1)]


def step5_abs(data):
    """Element-wise absolute value."""
    return [abs(x) for x in data]


def step6_sort_asc(data):
    """Sort in ascending order."""
    return sorted(data)


def step7_dedupe(data):
    """Remove duplicates, preserving order of first occurrence."""
    seen = set()
    result = [x for x in data if x not in seen and not seen.add(x)]
    return result


def step8_aggregate(data):
    """Compute sum, mean, count, min, max."""
    n = len(data)
    return {
        "sum": float(sum(data)),
        "mean": float(sum(data) / n),
        "count": int(n),
        "min": float(min(data)),
        "max": float(max(data)),
    }


def main():
    parser = argparse.ArgumentParser(description="lh04_ledger_roll pipeline step")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-8)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Read raw bytes for provenance, then parse JSON
    raw_bytes = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(raw_bytes).hexdigest()
    in_data = json.loads(raw_bytes)

    step = args.step

    # Step 1 reads from "values" key; steps 2-8 read from "data" key
    if step == 1:
        input_payload = in_data
        result = step1_parse(input_payload)
    else:
        input_payload = in_data["data"]
        if step == 2:
            result = step2_cumsum(input_payload)
        elif step == 3:
            result = step3_prefix_min(input_payload)
        elif step == 4:
            result = step4_diffs(input_payload)
        elif step == 5:
            result = step5_abs(input_payload)
        elif step == 6:
            result = step6_sort_asc(input_payload)
        elif step == 7:
            result = step7_dedupe(input_payload)
        elif step == 8:
            result = step8_aggregate(input_payload)
        else:
            raise ValueError(f"Unknown step: {step}")

    output = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }

    with open(args.out_path, "w") as f:
        f.write(json.dumps(output))


if __name__ == "__main__":
    main()
