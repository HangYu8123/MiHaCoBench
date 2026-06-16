"""Deliberately-broken reference for long_horizon/lh12_budget_forecast.

Planted defect (step 4 ONLY): the cumulative balance accumulates the monthly
nets in DESCENDING month order (latest -> earliest) instead of ascending, then
labels them with the ascending months. The running balances are therefore wrong,
which corrupts the slope/intercept fit in step 5 and cascades into the projection
(6), scenario (7), and summary (8). Steps 1-3 stay correct (partial credit).
MUST fail the grader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import accumulate

import numpy as np

INCOME_CATEGORIES = {"salary", "freelance", "bonus", "interest"}
N_PROJECT = 3
SCENARIO_FACTOR = 1.10


def step1_parse_sort(prev: dict) -> list:
    txns = list(prev["transactions"])
    return sorted(txns, key=lambda t: t["date"])


def step2_sign_normalize(prev: dict) -> list:
    out = []
    for t in prev["data"]:
        sign = 1.0 if t["category"] in INCOME_CATEGORIES else -1.0
        row = dict(t)
        row["net"] = round(sign * float(t["amount"]), 6)
        out.append(row)
    return out


def step3_monthly_net(prev: dict) -> dict:
    monthly: dict[str, float] = {}
    for t in prev["data"]:
        month = t["date"][:7]
        monthly[month] = round(monthly.get(month, 0.0) + float(t["net"]), 6)
    return monthly


def step4_cumulative_balance(prev: dict) -> list:
    monthly = prev["data"]
    months = sorted(monthly.keys())  # ascending labels
    # BUG: accumulate the nets in DESCENDING month order (reversed), so each
    # ascending-labelled month gets the wrong running balance.
    running_desc = list(accumulate(monthly[m] for m in reversed(months)))
    return [[m, round(bal, 6)] for m, bal in zip(months, running_desc)]


def step5_trend_fit(prev: dict) -> dict:
    balances = [row[1] for row in prev["data"]]
    idx = list(range(len(balances)))
    slope, intercept = np.polyfit(np.asarray(idx, dtype=float),
                                  np.asarray(balances, dtype=float), 1)
    return {
        "slope": round(float(slope), 6),
        "intercept": round(float(intercept), 6),
        "n_months": len(balances),
    }


def step6_project(prev: dict) -> dict:
    slope = float(prev["data"]["slope"])
    intercept = float(prev["data"]["intercept"])
    n = int(prev["data"]["n_months"])
    projection = [[i, round(slope * i + intercept, 6)] for i in range(n, n + N_PROJECT)]
    return {"projection": projection, "slope": round(slope, 6), "n_months": n}


def step7_scenario(prev: dict) -> dict:
    adjusted = [[i, round(val * SCENARIO_FACTOR, 6)] for i, val in prev["data"]["projection"]]
    return {
        "projection": adjusted,
        "slope": round(float(prev["data"]["slope"]), 6),
        "n_months": int(prev["data"]["n_months"]),
    }


def step8_summary(prev: dict) -> dict:
    adjusted = prev["data"]["projection"]
    return {
        "final_balance": round(float(adjusted[-1][1]), 6),
        "slope": round(float(prev["data"]["slope"]), 6),
        "n_months": int(prev["data"]["n_months"]),
    }


STEPS = {
    1: step1_parse_sort,
    2: step2_sign_normalize,
    3: step3_monthly_net,
    4: step4_cumulative_balance,
    5: step5_trend_fit,
    6: step6_project,
    7: step7_scenario,
    8: step8_summary,
}


def run_step(step: int, prev):
    return STEPS[step](prev)


def _provenance(in_path: str) -> str:
    return hashlib.sha256(open(in_path, "rb").read()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args(argv)

    prev = json.loads(open(args.in_path, encoding="utf-8").read())
    data = run_step(args.step, prev)
    out = {"step": args.step, "data": data, "provenance": _provenance(args.in_path)}
    with open(args.out_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
