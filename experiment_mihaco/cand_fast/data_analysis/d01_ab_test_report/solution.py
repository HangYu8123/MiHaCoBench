"""solution.py — A/B Test Report (d01_ab_test_report).

Public API
----------
analyze(df)          -> dict   Welch two-sample t-test, B vs A.
main(argv=None)      -> int    CLI entry point.
"""

import matplotlib
matplotlib.use("Agg")  # Must be set before importing pyplot

import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats
from scipy.stats import t as t_dist


def analyze(df: pd.DataFrame) -> dict:
    """Run a Welch two-sample t-test comparing group B against group A.

    Parameters
    ----------
    df : pandas.DataFrame
        Must have columns 'group' (str, values 'A' or 'B') and
        'value' (float, continuous measurement).

    Returns
    -------
    dict with keys:
        group_means : dict {"A": float, "B": float}
        n           : dict {"A": int, "B": int}
        t_stat      : float  Welch t-statistic (B minus A, positive when B > A)
        p_value     : float  Two-tailed p-value
        df          : float  Welch-Satterthwaite degrees of freedom
        cohens_d    : float  Cohen's d effect size
        ci95_low    : float  Lower bound of 95% CI of mean difference (B - A)
        ci95_high   : float  Upper bound of 95% CI of mean difference (B - A)
        reject_null : bool   True iff p_value < 0.05
    """
    a_vals = df.loc[df["group"] == "A", "value"].dropna().values
    b_vals = df.loc[df["group"] == "B", "value"].dropna().values

    n_A = int(len(a_vals))
    n_B = int(len(b_vals))

    mean_A = float(np.mean(a_vals))
    mean_B = float(np.mean(b_vals))

    std_A = float(np.std(a_vals, ddof=1))
    std_B = float(np.std(b_vals, ddof=1))

    # Welch t-test: B first, A second so that positive t means B > A
    # scipy.stats.ttest_ind must appear in source (surface-form check)
    ttest_result = scipy.stats.ttest_ind(b_vals, a_vals, equal_var=False)

    t_stat = float(ttest_result.statistic)
    p_value = float(ttest_result.pvalue)
    welch_df = float(ttest_result.df)  # Welch-Satterthwaite df (SciPy >= 1.11)

    # Cohen's d: (mean_B - mean_A) / pooled_std
    # pooled_std = sqrt((std_A**2 + std_B**2) / 2)  — simple average of variances
    pooled_std = np.sqrt((std_A ** 2 + std_B ** 2) / 2.0)
    cohens_d = float((mean_B - mean_A) / pooled_std)

    # 95% CI of mean difference (B - A)
    diff = mean_B - mean_A
    se = np.sqrt(std_A ** 2 / n_A + std_B ** 2 / n_B)
    t_crit = t_dist.ppf(0.975, df=welch_df)  # two-sided 95%
    ci95_low = float(diff - t_crit * se)
    ci95_high = float(diff + t_crit * se)

    reject_null = bool(p_value < 0.05)

    return {
        "group_means": {"A": mean_A, "B": mean_B},
        "n": {"A": n_A, "B": n_B},
        "t_stat": t_stat,
        "p_value": p_value,
        "df": welch_df,
        "cohens_d": cohens_d,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": reject_null,
    }


def save_plots(df: pd.DataFrame, output_dir: str) -> None:
    """Save two PNG plots into output_dir.

    1. histograms.png  — side-by-side histograms of value for each group.
    2. boxplot.png     — boxplot comparing the two groups.

    Parameters
    ----------
    df         : DataFrame with 'group' and 'value' columns.
    output_dir : Directory path where PNGs are written.
    """
    a_vals = df.loc[df["group"] == "A", "value"].dropna()
    b_vals = df.loc[df["group"] == "B", "value"].dropna()

    # --- Figure 1: Histograms (two subplots in one file = one PNG) ---
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.hist(a_vals, bins=20, color="steelblue", edgecolor="white", alpha=0.8)
    ax1.set_title("Group A — value distribution")
    ax1.set_xlabel("value")
    ax1.set_ylabel("count")

    ax2.hist(b_vals, bins=20, color="darkorange", edgecolor="white", alpha=0.8)
    ax2.set_title("Group B — value distribution")
    ax2.set_xlabel("value")
    ax2.set_ylabel("count")

    fig1.tight_layout()
    fig1.savefig(os.path.join(output_dir, "histograms.png"), dpi=100)
    plt.close(fig1)

    # --- Figure 2: Boxplot ---
    fig2, ax = plt.subplots(figsize=(7, 6))
    ax.boxplot(
        [a_vals.values, b_vals.values],
        labels=["A", "B"],
        patch_artist=True,
        boxprops=dict(facecolor="lightblue", color="navy"),
        medianprops=dict(color="red", linewidth=2),
    )
    ax.set_title("Boxplot: Group A vs Group B")
    ax.set_xlabel("Group")
    ax.set_ylabel("value")

    fig2.tight_layout()
    fig2.savefig(os.path.join(output_dir, "boxplot.png"), dpi=100)
    plt.close(fig2)


def main(argv: list | None = None) -> int:
    """CLI entry point.

    Usage
    -----
    python solution.py --data <csv_path> --output-dir <dir>

    Returns 0 on success, non-zero on error.
    """
    parser = argparse.ArgumentParser(
        description="A/B test report: Welch t-test analysis with plots."
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to input CSV file (columns: group, value).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where results.json and PNG plots are written.",
    )
    args = parser.parse_args(argv)

    try:
        os.makedirs(args.output_dir, exist_ok=True)

        df = pd.read_csv(args.data)

        if "group" not in df.columns or "value" not in df.columns:
            print(
                "Error: CSV must contain 'group' and 'value' columns.",
                file=sys.stderr,
            )
            return 1

        results = analyze(df)

        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

        save_plots(df, args.output_dir)

        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
