"""
Budget Forecast Pipeline — 8-step chain
Usage: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys

import numpy as np


INCOME_CATEGORIES = {"salary", "freelance", "bonus", "interest"}


def compute_provenance(in_path: str) -> str:
    raw = open(in_path, "rb").read()
    return hashlib.sha256(raw).hexdigest()


def write_output(out_path: str, step: int, data, provenance: str) -> None:
    result = {"step": step, "data": data, "provenance": provenance}
    with open(out_path, "w") as f:
        json.dump(result, f)


def round6(x):
    return round(x, 6)


def step1_parse_sort(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        raw = json.load(f)
    transactions = raw["transactions"]
    sorted_transactions = sorted(transactions, key=lambda r: r["date"])
    write_output(out_path, 1, sorted_transactions, provenance)


def step2_sign_normalize(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        artifact = json.load(f)
    rows = artifact["data"]
    result = []
    for row in rows:
        row_copy = dict(row)
        cat = row_copy.get("category", "")
        amount = row_copy["amount"]
        if cat in INCOME_CATEGORIES:
            net = round6(float(amount))
        else:
            net = round6(-float(amount))
        row_copy["net"] = net
        result.append(row_copy)
    write_output(out_path, 2, result, provenance)


def step3_monthly_net(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        artifact = json.load(f)
    rows = artifact["data"]
    # accumulate in order (rows already sorted by date from step 1)
    monthly = {}
    for row in rows:
        month = row["date"][:7]
        net = float(row["net"])
        if month not in monthly:
            monthly[month] = 0.0
        monthly[month] += net
    # sort ascending by month key
    sorted_monthly = {k: round6(v) for k, v in sorted(monthly.items())}
    write_output(out_path, 3, sorted_monthly, provenance)


def step4_cumulative_balance(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        artifact = json.load(f)
    monthly = artifact["data"]
    # sort by month key ascending
    sorted_months = sorted(monthly.items())
    result = []
    running = 0.0
    for month, net in sorted_months:
        running += float(net)
        result.append([month, round6(running)])
    write_output(out_path, 4, result, provenance)


def step5_trend_fit(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        artifact = json.load(f)
    pairs = artifact["data"]
    n_months = len(pairs)
    indices = np.array(range(n_months), dtype=float)
    balances = np.array([p[1] for p in pairs], dtype=float)
    coeffs = np.polyfit(indices, balances, 1)
    slope = round6(float(coeffs[0]))
    intercept = round6(float(coeffs[1]))
    data = {"slope": slope, "intercept": intercept, "n_months": n_months}
    write_output(out_path, 5, data, provenance)


def step6_project(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        artifact = json.load(f)
    trend = artifact["data"]
    slope = float(trend["slope"])
    intercept = float(trend["intercept"])
    n_months = int(trend["n_months"])
    projection = []
    for i in range(n_months, n_months + 3):
        projected_balance = round6(slope * i + intercept)
        projection.append([i, projected_balance])
    data = {
        "projection": projection,
        "slope": round6(slope),
        "n_months": n_months,
    }
    write_output(out_path, 6, data, provenance)


def step7_scenario(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        artifact = json.load(f)
    proj_data = artifact["data"]
    slope = float(proj_data["slope"])
    n_months = int(proj_data["n_months"])
    projection = proj_data["projection"]
    adjusted = []
    for entry in projection:
        idx = entry[0]
        bal = float(entry[1])
        adjusted_bal = round6(bal * 1.10)
        adjusted.append([idx, adjusted_bal])
    data = {
        "projection": adjusted,
        "slope": round6(slope),
        "n_months": n_months,
    }
    write_output(out_path, 7, data, provenance)


def step8_summary(in_path: str, out_path: str) -> None:
    provenance = compute_provenance(in_path)
    with open(in_path, "r") as f:
        artifact = json.load(f)
    proj_data = artifact["data"]
    slope = float(proj_data["slope"])
    n_months = int(proj_data["n_months"])
    projection = proj_data["projection"]
    final_balance = round6(float(projection[-1][1]))
    data = {
        "final_balance": final_balance,
        "slope": round6(slope),
        "n_months": n_months,
    }
    write_output(out_path, 8, data, provenance)


STEP_HANDLERS = {
    1: step1_parse_sort,
    2: step2_sign_normalize,
    3: step3_monthly_net,
    4: step4_cumulative_balance,
    5: step5_trend_fit,
    6: step6_project,
    7: step7_scenario,
    8: step8_summary,
}


def main():
    parser = argparse.ArgumentParser(description="Budget Forecast Pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-8)")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON path")
    args = parser.parse_args()

    if args.step not in STEP_HANDLERS:
        print(f"Unknown step: {args.step}. Must be 1-8.", file=sys.stderr)
        sys.exit(1)

    STEP_HANDLERS[args.step](args.in_path, args.out_path)


if __name__ == "__main__":
    main()
