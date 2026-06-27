import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


def analyze(df: pd.DataFrame) -> dict:
    """Analyze survey data with contingency table, chi-squared test, and bootstrap CI."""
    # Validate required columns
    if "group" not in df.columns or "response" not in df.columns:
        raise KeyError("DataFrame must contain 'group' and 'response' columns")

    # 1. Build contingency table using pandas.crosstab
    ct = pd.crosstab(df["group"], df["response"])

    # Ensure all expected response categories are present
    for col in ["yes", "no", "maybe"]:
        if col not in ct.columns:
            ct[col] = 0

    # Ensure both groups are present
    for row in ["control", "treatment"]:
        if row not in ct.index:
            ct.loc[row] = 0

    # Reorder for consistency
    ct = ct.loc[["control", "treatment"], ["yes", "no", "maybe"]]

    # Build table dict with plain int values
    table = {
        group: {resp: int(ct.loc[group, resp]) for resp in ["yes", "no", "maybe"]}
        for group in ["control", "treatment"]
    }

    # 2. Chi-squared test (no continuity correction)
    chi2_stat, p_val, dof, _ = chi2_contingency(ct, correction=False)

    # 3. Cramér's V
    n = len(df)
    r, c = ct.shape  # r=2 groups, c=3 responses
    cramers_v = np.sqrt(chi2_stat / (n * (min(r, c) - 1)))

    # 4. Bootstrap 95% CI for yes-rate difference (treatment - control)
    control_responses = df[df["group"] == "control"]["response"].values
    treatment_responses = df[df["group"] == "treatment"]["response"].values

    n_control = len(control_responses)
    n_treatment = len(treatment_responses)

    rng = np.random.default_rng(42)
    n_resamples = 1000
    boot_diffs = np.empty(n_resamples)

    for i in range(n_resamples):
        ctrl_sample = rng.choice(control_responses, size=n_control, replace=True)
        treat_sample = rng.choice(treatment_responses, size=n_treatment, replace=True)
        yes_rate_control = np.sum(ctrl_sample == "yes") / n_control
        yes_rate_treatment = np.sum(treat_sample == "yes") / n_treatment
        boot_diffs[i] = yes_rate_treatment - yes_rate_control

    ci95_low = float(np.percentile(boot_diffs, 2.5))
    ci95_high = float(np.percentile(boot_diffs, 97.5))

    return {
        "table": table,
        "chi2": float(chi2_stat),
        "dof": int(dof),
        "p_value": float(p_val),
        "cramers_v": float(cramers_v),
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": bool(p_val < 0.05),
    }
