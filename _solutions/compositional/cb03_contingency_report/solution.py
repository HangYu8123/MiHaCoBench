"""Gold reference for compositional/cb03_contingency_report.

Compose pandas (crosstab), scipy.stats (chi2_contingency),
numpy (bootstrap) to produce a contingency report dict.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Analyze group × response contingency table.

    Parameters
    ----------
    df:
        DataFrame with columns ``group`` (str: control/treatment) and
        ``response`` (str: yes/no/maybe).

    Returns
    -------
    dict with keys: table, chi2, dof, p_value, cramers_v,
    ci95_low, ci95_high, reject_null.

    Raises
    ------
    KeyError / ValueError if required columns are missing.
    """
    # Validate required columns
    for col in ("group", "response"):
        if col not in df.columns:
            raise KeyError(f"Missing required column: '{col}'")

    # --- 1. Contingency table via pandas.crosstab ---
    ct = pd.crosstab(df["group"], df["response"])

    # Build nested dict: table[group][response] = count
    table: dict[str, dict[str, int]] = {}
    for grp in ct.index:
        table[str(grp)] = {str(resp): int(ct.loc[grp, resp]) for resp in ct.columns}

    # --- 2. Chi-squared test ---
    chi2_stat, p_val, dof, _ = scipy.stats.chi2_contingency(
        ct.values, correction=False
    )
    chi2_stat = float(chi2_stat)
    p_val = float(p_val)
    dof = int(dof)

    # --- 3. Cramér's V ---
    n = int(df.shape[0])
    r, c = ct.shape  # rows = groups, columns = responses
    cramers_v = float(math.sqrt(chi2_stat / (n * (min(r, c) - 1))))

    # --- 4. Bootstrap 95 % CI for yes-rate difference (treatment - control) ---
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
