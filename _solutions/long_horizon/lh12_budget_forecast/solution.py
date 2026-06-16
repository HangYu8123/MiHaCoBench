"""Gold reference for long_horizon/lh12_budget_forecast — an 8-step provenance chain.

A budget forecast pipeline. Each step is run separately and consumes ONLY the
artifact written by the previous step (step 1 reads the original transactions
file). Each step writes JSON of the shape
``{"step": K, "data": <result>, "provenance": <sha256 of the --in file>}``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import accumulate

import numpy as np

# Fixed category -> sign map. Income is positive, everything else (including
# unknown categories) is treated as an expense (negative).
INCOME_CATEGORIES = {"salary", "freelance", "bonus", "interest"}

# Number of future month indices to project.
N_PROJECT = 3
# Savings-scenario multiplier (+10%).
SCENARIO_FACTOR = 1.10


def step1_parse_sort(prev: dict) -> list:
    """Return the transaction rows sorted ascending by ISO date string."""
    txns = list(prev["transactions"])
    return sorted(txns, key=lambda t: t["date"])


def step2_sign_normalize(prev: dict) -> list:
    """Attach a signed ``net`` per txn: income positive, otherwise negative."""
    out = []
    for t in prev["data"]:
        sign = 1.0 if t["category"] in INCOME_CATEGORIES else -1.0
        row = dict(t)
        row["net"] = round(sign * float(t["amount"]), 6)
        out.append(row)
    return out


def step3_monthly_net(prev: dict) -> dict:
    """Aggregate the signed nets into a {``YYYY-MM``: net_sum} dict."""
    monthly: dict[str, float] = {}
    for t in prev["data"]:
        month = t["date"][:7]
        monthly[month] = round(monthly.get(month, 0.0) + float(t["net"]), 6)
    return monthly


def step4_cumulative_balance(prev: dict) -> list:
    """Running balance per month in ASCENDING month order (earliest -> latest)."""
    monthly = prev["data"]
    months = sorted(monthly.keys())  # ascending: earliest -> latest
    running = list(accumulate(monthly[m] for m in months))
    return [[m, round(bal, 6)] for m, bal in zip(months, running)]


def step5_trend_fit(prev: dict) -> dict:
    """Fit balance ~ slope * month_index + intercept via numpy.polyfit(deg=1).

    Also carries ``n_months`` so the projection step knows where history ends.
    """
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
    """Project the next 3 month indices using the fitted line.

    Carries ``slope``/``n_months`` forward so the final summary can report them.
    """
    slope = float(prev["data"]["slope"])
    intercept = float(prev["data"]["intercept"])
    n = int(prev["data"]["n_months"])
    projection = [[i, round(slope * i + intercept, 6)] for i in range(n, n + N_PROJECT)]
    return {"projection": projection, "slope": round(slope, 6), "n_months": n}


def step7_scenario(prev: dict) -> dict:
    """Apply a +10% savings scenario: multiply each projected balance by 1.10."""
    adjusted = [[i, round(val * SCENARIO_FACTOR, 6)] for i, val in prev["data"]["projection"]]
    return {
        "projection": adjusted,
        "slope": round(float(prev["data"]["slope"]), 6),
        "n_months": int(prev["data"]["n_months"]),
    }


def step8_summary(prev: dict) -> dict:
    """Summarise: final adjusted balance, slope, and number of historical months."""
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
    """Dispatch to the transform for ``step``."""
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
