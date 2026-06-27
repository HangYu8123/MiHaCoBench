"""
Budget Forecast Pipeline — 8-step chain.
Usage: python solution.py --step <K> --in <input_json_path> --out <output_json_path>
"""
import argparse
import hashlib
import json
import collections
import itertools

import numpy as np


INCOME_CATEGORIES = {"salary", "freelance", "bonus", "interest"}


def provenance(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def write_output(out_path: str, step: int, data, prov: str) -> None:
    result = {"step": step, "data": data, "provenance": prov}
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False))


# ── Step 1: parse_sort ────────────────────────────────────────────────────────
def step_parse_sort(raw_bytes: bytes) -> list:
    payload = json.loads(raw_bytes)
    transactions = payload["transactions"]
    return sorted(transactions, key=lambda r: r["date"])


# ── Step 2: sign_normalize ────────────────────────────────────────────────────
def step_sign_normalize(raw_bytes: bytes) -> list:
    payload = json.loads(raw_bytes)
    rows = payload["data"]
    result = []
    for row in rows:
        amount = row["amount"]
        category = row["category"]
        net = amount if category in INCOME_CATEGORIES else -amount
        # Do NOT round individual net values here — only round aggregates later.
        new_row = dict(row)
        new_row["net"] = net
        result.append(new_row)
    return result


# ── Step 3: monthly_net ───────────────────────────────────────────────────────
def step_monthly_net(raw_bytes: bytes) -> dict:
    payload = json.loads(raw_bytes)
    rows = payload["data"]
    monthly = collections.defaultdict(float)
    for row in rows:
        month = row["date"][:7]
        monthly[month] += row["net"]
    # Sort keys ascending, round values to 6 decimals.
    return {k: round(monthly[k], 6) for k in sorted(monthly.keys())}


# ── Step 4: cumulative_balance ────────────────────────────────────────────────
def step_cumulative_balance(raw_bytes: bytes) -> list:
    payload = json.loads(raw_bytes)
    monthly_net = payload["data"]
    # Keys already sorted ascending (step 3 guarantees this), but sort again for safety.
    sorted_months = sorted(monthly_net.keys())
    result = []
    running = 0.0
    for month in sorted_months:
        running += monthly_net[month]
        result.append([month, round(running, 6)])
    return result


# ── Step 5: trend_fit ─────────────────────────────────────────────────────────
def step_trend_fit(raw_bytes: bytes) -> dict:
    payload = json.loads(raw_bytes)
    pairs = payload["data"]  # [[month, balance], ...]
    n = len(pairs)
    idx = list(range(n))
    balances = [p[1] for p in pairs]
    coeffs = np.polyfit(idx, balances, 1)  # [slope, intercept], highest degree first
    slope = float(coeffs[0])
    intercept = float(coeffs[1])
    return {
        "slope": round(slope, 6),
        "intercept": round(intercept, 6),
        "n_months": n,
    }


# ── Step 6: project ───────────────────────────────────────────────────────────
def step_project(raw_bytes: bytes) -> dict:
    payload = json.loads(raw_bytes)
    d = payload["data"]
    slope = d["slope"]
    intercept = d["intercept"]
    n_months = d["n_months"]
    projection = []
    for i in range(n_months, n_months + 3):
        bal = slope * i + intercept
        projection.append([i, round(bal, 6)])
    return {
        "projection": projection,
        "slope": slope,
        "n_months": n_months,
    }


# ── Step 7: scenario ──────────────────────────────────────────────────────────
def step_scenario(raw_bytes: bytes) -> dict:
    payload = json.loads(raw_bytes)
    d = payload["data"]
    slope = d["slope"]
    n_months = d["n_months"]
    projection = d["projection"]
    adjusted = [[idx, round(bal * 1.10, 6)] for idx, bal in projection]
    return {
        "projection": adjusted,
        "slope": slope,
        "n_months": n_months,
    }


# ── Step 8: summary ───────────────────────────────────────────────────────────
def step_summary(raw_bytes: bytes) -> dict:
    payload = json.loads(raw_bytes)
    d = payload["data"]
    slope = d["slope"]
    n_months = d["n_months"]
    projection = d["projection"]
    final_balance = projection[-1][1]  # last element's adjusted balance
    return {
        "final_balance": round(final_balance, 6),
        "slope": slope,
        "n_months": n_months,
    }


# ── Dispatch ──────────────────────────────────────────────────────────────────
STEPS = {
    1: step_parse_sort,
    2: step_sign_normalize,
    3: step_monthly_net,
    4: step_cumulative_balance,
    5: step_trend_fit,
    6: step_project,
    7: step_scenario,
    8: step_summary,
}


def main():
    parser = argparse.ArgumentParser(description="Budget forecast pipeline")
    parser.add_argument("--step", type=int, required=True, help="Step number (1-8)")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON path")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    if args.step not in STEPS:
        raise ValueError(f"Unknown step: {args.step}. Must be 1-8.")

    # Read file bytes once; compute provenance from exact bytes.
    raw_bytes = open(args.input, "rb").read()
    prov = provenance(raw_bytes)

    # Compute result.
    fn = STEPS[args.step]
    data = fn(raw_bytes)

    # Write output.
    write_output(args.out, args.step, data, prov)


if __name__ == "__main__":
    main()
