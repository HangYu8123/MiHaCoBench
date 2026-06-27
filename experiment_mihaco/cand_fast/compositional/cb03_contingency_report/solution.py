import math

import numpy as np
import pandas as pd
from scipy import stats


def analyze(df: pd.DataFrame) -> dict:
    # Validate required columns
    if "group" not in df.columns:
        raise KeyError("group")
    if "response" not in df.columns:
        raise KeyError("response")

    # Build contingency table with all expected labels
    table_df = pd.crosstab(df["group"], df["response"])
    table_df = table_df.reindex(
        index=["control", "treatment"],
        columns=["yes", "no", "maybe"],
        fill_value=0,
    )

    # Convert to nested dict with plain Python int values
    table = {
        group: {resp: int(count) for resp, count in row.items()}
        for group, row in table_df.to_dict(orient="index").items()
    }

    # Chi-squared test (no continuity correction)
    chi2_stat, p_value, dof, _expected = stats.chi2_contingency(table_df, correction=False)
    chi2_stat = float(chi2_stat)
    p_value = float(p_value)
    dof = int(dof)

    # Cramér's V
    n = df.shape[0]
    r, c = table_df.shape
    cramers_v = math.sqrt(chi2_stat / (n * (min(r, c) - 1)))

    # Bootstrap 95% CI for yes-rate difference (treatment - control)
    control_responses = df.loc[df["group"] == "control", "response"].values
    treatment_responses = df.loc[df["group"] == "treatment", "response"].values

    np.random.seed(42)
    diffs = []
    for _ in range(1000):
        ctrl = np.random.choice(control_responses, size=len(control_responses), replace=True)
        trt = np.random.choice(treatment_responses, size=len(treatment_responses), replace=True)
        diffs.append((trt == "yes").mean() - (ctrl == "yes").mean())

    ci95_low, ci95_high = np.percentile(diffs, [2.5, 97.5])

    return {
        "table": table,
        "chi2": chi2_stat,
        "dof": dof,
        "p_value": p_value,
        "cramers_v": float(cramers_v),
        "ci95_low": float(ci95_low),
        "ci95_high": float(ci95_high),
        "reject_null": bool(p_value < 0.05),
    }
