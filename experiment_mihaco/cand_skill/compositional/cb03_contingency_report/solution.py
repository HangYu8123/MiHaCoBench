"""
cb03_contingency_report — Survey Contingency Analysis
"""

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze a survey DataFrame with 'group' and 'response' columns.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns 'group' (values: 'control', 'treatment') and
        'response' (values: 'yes', 'no', 'maybe').

    Returns
    -------
    dict with keys: table, chi2, dof, p_value, cramers_v,
                    ci95_low, ci95_high, reject_null
    """
    # --- Task 1: Validate inputs ---
    if "group" not in df.columns or "response" not in df.columns:
        raise KeyError(
            "DataFrame must contain both 'group' and 'response' columns."
        )

    # --- Task 2: Build contingency table ---
    ct = pd.crosstab(df["group"], df["response"])
    # Reindex to ensure all expected categories are present (fill missing with 0)
    ct = ct.reindex(
        index=["control", "treatment"],
        columns=["yes", "no", "maybe"],
        fill_value=0,
    )

    # Convert to nested dict with plain Python ints
    table = {
        grp: {col: int(ct.loc[grp, col]) for col in ["yes", "no", "maybe"]}
        for grp in ["control", "treatment"]
    }

    # --- Task 3: Chi-squared test ---
    chi2_stat, p_value, dof, _expected = chi2_contingency(
        ct.values, correction=False
    )
    dof = int(dof)
    reject_null = bool(p_value < 0.05)

    # --- Task 4: Cramér's V ---
    n = df.shape[0]
    r, c = ct.shape  # r=2 groups, c=3 responses
    cramers_v = float(np.sqrt(chi2_stat / (n * (min(r, c) - 1))))

    # --- Task 5: Bootstrap 95% CI for yes-rate difference (treatment - control) ---
    np.random.seed(42)

    ctrl_mask = df["group"] == "control"
    trt_mask = df["group"] == "treatment"

    ctrl_responses = df.loc[ctrl_mask, "response"].values
    trt_responses = df.loc[trt_mask, "response"].values

    n_ctrl = len(ctrl_responses)
    n_trt = len(trt_responses)

    diffs = []
    for _ in range(1000):
        ctrl_sample = np.random.choice(ctrl_responses, size=n_ctrl, replace=True)
        trt_sample = np.random.choice(trt_responses, size=n_trt, replace=True)
        yes_rate_ctrl = float(np.mean(ctrl_sample == "yes"))
        yes_rate_trt = float(np.mean(trt_sample == "yes"))
        diffs.append(yes_rate_trt - yes_rate_ctrl)

    ci95_low, ci95_high = np.percentile(diffs, [2.5, 97.5])

    return {
        "table": table,
        "chi2": float(chi2_stat),
        "dof": dof,
        "p_value": float(p_value),
        "cramers_v": cramers_v,
        "ci95_low": float(ci95_low),
        "ci95_high": float(ci95_high),
        "reject_null": reject_null,
    }
