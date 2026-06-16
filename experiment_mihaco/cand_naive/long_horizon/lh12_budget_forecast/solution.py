"""
Budget Forecast Pipeline — 8-step chain.

Usage:
    python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""

import argparse
import hashlib
import json
import sys

import numpy as np

INCOME_CATEGORIES = {"salary", "freelance", "bonus", "interest"}


def compute_provenance(in_path: str) -> str:
    with open(in_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def round6(v):
    return round(float(v), 6)


def step1_parse_sort(data):
    """Read transactions list and sort ascending by date."""
    transactions = data["transactions"]
    sorted_txns = sorted(transactions, key=lambda x: x["date"])
    return sorted_txns


def step2_sign_normalize(data):
    """Augment each row with a signed 'net' field."""
    rows = data["data"]
    result = []
    for row in rows:
        new_row = dict(row)
        category = row.get("category", "")
        amount = float(row["amount"])
        if category in INCOME_CATEGORIES:
            net = round6(amount)
        else:
            net = round6(-amount)
        new_row["net"] = net
        result.append(new_row)
    return result


def step3_monthly_net(data):
    """Sum net per calendar month."""
    rows = data["data"]
    monthly = {}
    for row in rows:
        month = row["date"][:7]
        monthly[month] = monthly.get(month, 0.0) + row["net"]
    # Round values
    return {k: round6(v) for k, v in monthly.items()}


def step4_cumulative_balance(data):
    """Running cumulative sum of monthly nets in ascending month order."""
    monthly = data["data"]
    sorted_months = sorted(monthly.keys())
    result = []
    running = 0.0
    for month in sorted_months:
        running += monthly[month]
        result.append([month, round6(running)])
    return result


def step5_trend_fit(data):
    """Fit balance ~ slope * month_index + intercept using numpy.polyfit."""
    pairs = data["data"]  # list of [month, balance]
    n = len(pairs)
    idx = np.arange(n, dtype=float)
    balances = np.array([p[1] for p in pairs], dtype=float)
    coeffs = np.polyfit(idx, balances, 1)
    slope = round6(coeffs[0])
    intercept = round6(coeffs[1])
    return {"slope": slope, "intercept": intercept, "n_months": n}


def step6_project(data):
    """Project the next 3 month indices beyond historical data."""
    d = data["data"]
    slope = d["slope"]
    intercept = d["intercept"]
    n_months = d["n_months"]
    projection = []
    for i in range(3):
        idx = n_months + i
        projected = round6(slope * idx + intercept)
        projection.append([idx, projected])
    return {"projection": projection, "slope": slope, "n_months": n_months}


def step7_scenario(data):
    """Apply +10% savings scenario: multiply each projected balance by 1.10."""
    d = data["data"]
    projection = d["projection"]
    slope = d["slope"]
    n_months = d["n_months"]
    adjusted = [[idx, round6(bal * 1.10)] for idx, bal in projection]
    return {"projection": adjusted, "slope": slope, "n_months": n_months}


def step8_summary(data):
    """Summarize: final balance, slope, n_months."""
    d = data["data"]
    projection = d["projection"]
    slope = d["slope"]
    n_months = d["n_months"]
    final_balance = round6(projection[-1][1])
    return {"final_balance": final_balance, "slope": slope, "n_months": n_months}


STEP_FUNCTIONS = {
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    step_k = args.step
    in_path = args.in_path
    out_path = args.out_path

    provenance = compute_provenance(in_path)

    with open(in_path, "r", encoding="utf-8") as f:
        in_data = json.load(f)

    if step_k not in STEP_FUNCTIONS:
        print(f"Unknown step: {step_k}", file=sys.stderr)
        sys.exit(1)

    fn = STEP_FUNCTIONS[step_k]
    result = fn(in_data)

    out_obj = {"step": step_k, "data": result, "provenance": provenance}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f)


if __name__ == "__main__":
    main()
