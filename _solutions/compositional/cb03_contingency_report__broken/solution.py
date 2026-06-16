"""BROKEN reference for compositional/cb03_contingency_report.

Localized defect: the chi-squared test is run on a collapsed 2-column
table (yes vs not-yes) instead of the full 3-column table.
This produces a wrong chi2 statistic AND wrong dof (1 instead of 2),
while the contingency table itself is reported correctly.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Analyze group x response contingency — BROKEN variant.

    Defect: chi2_contingency is called on a collapsed 2-column table
    (yes vs not-yes), giving wrong chi2 and dof=1 instead of dof=2.
    The 'table' key is still computed correctly from the full crosstab.
    """
    for col in ("group", "response"):
        if col not in df.columns:
            raise KeyError(f"Missing required column: '{col}'")

    # Correct contingency table (not broken)
    ct = pd.crosstab(df["group"], df["response"])
    table: dict[str, dict[str, int]] = {}
    for grp in ct.index:
        table[str(grp)] = {str(resp): int(ct.loc[grp, resp]) for resp in ct.columns}

    # --- DEFECT: collapse 'no' + 'maybe' into a single category,
    #     then run chi2 on this 2-column table.
    #     This gives dof=1 (wrong) and a different chi2 (wrong). ---
    ct_collapsed = ct[["yes"]].copy()
    ct_collapsed["not_yes"] = ct.drop(columns=["yes"]).sum(axis=1)
    chi2_stat, p_val, dof, _ = scipy.stats.chi2_contingency(
        ct_collapsed.values, correction=False
    )
    chi2_stat = float(chi2_stat)
    p_val = float(p_val)
    dof = int(dof)   # will be 1, not 2

    # Cramér's V — uses wrong chi2 and wrong min(r,c)-1
    n = int(df.shape[0])
    r, c = ct_collapsed.shape   # c=2, so min(r,c)-1 = 1 (by coincidence correct here)
    cramers_v = float(math.sqrt(chi2_stat / (n * (min(r, c) - 1))))

    # Bootstrap CI (correct, not broken)
    rng = np.random.default_rng(42)
    ctrl_arr = (df.loc[df["group"] == "control", "response"] == "yes").values.astype(
        np.float64
    )
    trt_arr = (df.loc[df["group"] == "treatment", "response"] == "yes").values.astype(
        np.float64
    )
    n_ctrl = len(ctrl_arr)
    n_trt = len(trt_arr)
    n_boot = 1000
    boot_diffs = np.empty(n_boot)
    for i in range(n_boot):
        boot_ctrl = rng.choice(ctrl_arr, size=n_ctrl, replace=True)
        boot_trt = rng.choice(trt_arr, size=n_trt, replace=True)
        boot_diffs[i] = boot_trt.mean() - boot_ctrl.mean()

    ci95_low = float(np.percentile(boot_diffs, 2.5))
    ci95_high = float(np.percentile(boot_diffs, 97.5))

    reject_null = bool(p_val < 0.05)

    return {
        "table": table,
        "chi2": chi2_stat,
        "dof": dof,
        "p_value": p_val,
        "cramers_v": cramers_v,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": reject_null,
    }
