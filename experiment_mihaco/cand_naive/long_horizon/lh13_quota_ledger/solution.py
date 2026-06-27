import argparse
import hashlib
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    in_bytes = open(args.in_path, "rb").read()
    provenance = hashlib.sha256(in_bytes).hexdigest()
    in_json = json.loads(in_bytes)

    step = args.step

    if step == 1:
        # Reads input.json directly: {"budget": ..., "requests": [...]}
        budget = in_json["budget"]
        requests = in_json["requests"]
        data = {
            "budget": budget,
            "remaining": budget,
            "queue": requests,
            "committed": [],
        }
    elif 2 <= step <= 9:
        # Reads previous step's full artifact; state is under "data"
        prev_data = in_json["data"]
        budget = prev_data["budget"]
        remaining = prev_data["remaining"]
        queue = prev_data["queue"]
        committed = prev_data["committed"]

        # Pop the front request
        request = queue[0]
        rest = queue[1:]

        req_id = request["id"]
        amount = request["amount"]
        g = min(amount, remaining)
        remaining = remaining - g

        committed = committed + [{"id": req_id, "requested": amount, "granted": g}]

        data = {
            "budget": budget,
            "remaining": remaining,
            "queue": rest,
            "committed": committed,
        }
    elif step == 10:
        # Reconcile
        prev_data = in_json["data"]
        budget = prev_data["budget"]
        remaining = prev_data["remaining"]
        committed = prev_data["committed"]

        total_granted = sum(c["granted"] for c in committed)
        fully_granted = sum(1 for c in committed if c["granted"] == c["requested"])
        partial = sum(1 for c in committed if 0 < c["granted"] < c["requested"])
        rejected = sum(1 for c in committed if c["granted"] == 0)
        utilization = total_granted / budget if budget != 0 else 0.0
        reconciled = (total_granted + remaining) == budget

        data = {
            "budget": budget,
            "total_granted": total_granted,
            "remaining": remaining,
            "utilization": utilization,
            "fully_granted": fully_granted,
            "partial": partial,
            "rejected": rejected,
            "reconciled": reconciled,
        }
    else:
        raise ValueError(f"Unknown step: {step}")

    result = {"step": step, "data": data, "provenance": provenance}

    with open(args.out_path, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
