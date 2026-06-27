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


def sha256_of_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def round6(x):
    return round(float(x), 6)


def step1_parse_sort(data):
    """Read transactions list and sort ascending by date."""
    transactions = data["transactions"]
    sorted_txns = sorted(transactions, key=lambda r: r["date"])
    return sorted_txns


def step2_sign_normalize(data):
    """Augment each row with a signed 'net' field."""
    rows = data  # list from step 1
    result = []
    for row in rows:
        row = dict(row)
        amount = float(row["amount"])
        if row["category"] in INCOME_CATEGORIES:
            net = round6(amount)
        else:
            net = round6(-amount)
        row["net"] = net
        result.append(row)
    return result


def step3_monthly_net(data):
    """Sum net per calendar month."""
    rows = data  # list from step 2
    monthly = {}
    for row in rows:
        month = row["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0.0) + float(row["net"])
    # Round values
    return {k: round6(v) for k, v in monthly.items()}


def step4_cumulative_balance(data):
    """Compute cumulative balance in ascending month order."""
    monthly = data  # dict from step 3
    sorted_months = sorted(monthly.keys())
    result = []
    running = 0.0
    for month in sorted_months:
        running += float(monthly[month])
        result.append([month, round6(running)])
    return result


def step5_trend_fit(data):
    """Fit balance ~ slope * month_index + intercept using numpy.polyfit."""
    pairs = data  # list of [month, balance] from step 4
    n = len(pairs)
    indices = np.arange(n, dtype=float)
    balances = np.array([p[1] for p in pairs], dtype=float)
    coeffs = np.polyfit(indices, balances, 1)
    slope = round6(coeffs[0])
    intercept = round6(coeffs[1])
    return {"slope": slope, "intercept": intercept, "n_months": n}


def step6_project(data):
    """Project the next 3 months using the fitted line."""
    slope = float(data["slope"])
    intercept = float(data["intercept"])
    n_months = int(data["n_months"])
    projection = []
    for i in range(n_months, n_months + 3):
        projected = round6(slope * i + intercept)
        projection.append([i, projected])
    return {"projection": projection, "slope": round6(slope), "n_months": n_months}


def step7_scenario(data):
    """Apply +10% savings scenario: multiply each projected balance by 1.10."""
    projection = data["projection"]
    slope = data["slope"]
    n_months = data["n_months"]
    adjusted = [[idx, round6(bal * 1.10)] for idx, bal in projection]
    return {"projection": adjusted, "slope": round6(float(slope)), "n_months": int(n_months)}


def step8_summary(data):
    """Summarize with final_balance, slope, n_months."""
    projection = data["projection"]
    slope = data["slope"]
    n_months = data["n_months"]
    final_balance = round6(projection[-1][1])
    return {"final_balance": final_balance, "slope": round6(float(slope)), "n_months": int(n_months)}


STEP_FUNCS = {
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
    parser.add_argument("--in", dest="input", required=True)
    parser.add_argument("--out", dest="output", required=True)
    args = parser.parse_args()

    in_path = args.input
    out_path = args.output
    step = args.step

    # Compute provenance from the input file bytes
    provenance = sha256_of_file(in_path)

    # Read input JSON
    with open(in_path, "r", encoding="utf-8") as f:
        in_json = json.load(f)

    # For step 1, input has "transactions" key; for later steps, use "data" key
    if step == 1:
        data = in_json
    else:
        data = in_json["data"]

    # Run the step function
    func = STEP_FUNCS[step]
    result = func(data)

    # Write output
    out_obj = {
        "step": step,
        "data": result,
        "provenance": provenance,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f)


if __name__ == "__main__":
    main()
