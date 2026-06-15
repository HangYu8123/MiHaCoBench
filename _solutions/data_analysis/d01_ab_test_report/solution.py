"""Gold reference for data_analysis/d01_ab_test_report — A/B test analysis."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Run a Welch two-sample t-test comparing group B vs group A.

    Returns a dict with keys: group_means, n, t_stat, p_value, df,
    cohens_d, ci95_low, ci95_high, reject_null.
    B-minus-A orientation: positive t_stat means B > A.
    """
    a_vals = df.loc[df["group"] == "A", "value"].values
    b_vals = df.loc[df["group"] == "B", "value"].values

    mean_a = float(np.mean(a_vals))
    mean_b = float(np.mean(b_vals))
    n_a = int(len(a_vals))
    n_b = int(len(b_vals))

    # Welch t-test: B vs A (so statistic is positive when mean_B > mean_A)
    t_stat, p_value = scipy.stats.ttest_ind(b_vals, a_vals, equal_var=False)
    t_stat = float(t_stat)
    p_value = float(p_value)

    # Degrees of freedom (Welch–Satterthwaite) — scipy returns it via ttest_ind_from_stats
    std_a = float(np.std(a_vals, ddof=1))
    std_b = float(np.std(b_vals, ddof=1))

    var_a = std_a ** 2
    var_b = std_b ** 2

    # Welch–Satterthwaite df
    se_sq_a = var_a / n_a
    se_sq_b = var_b / n_b
    se_sq = se_sq_a + se_sq_b
    welch_df = float(se_sq ** 2 / (se_sq_a ** 2 / (n_a - 1) + se_sq_b ** 2 / (n_b - 1)))

    # Cohen's d using pooled std (sqrt of average of sample variances)
    pooled_std = math.sqrt((var_a + var_b) / 2.0)
    cohens_d = float((mean_b - mean_a) / pooled_std)

    # 95% CI of mean difference (B - A)
    diff = mean_b - mean_a
    se = math.sqrt(var_a / n_a + var_b / n_b)
    t_crit = float(scipy.stats.t.ppf(0.975, df=welch_df))
    ci95_low = float(diff - t_crit * se)
    ci95_high = float(diff + t_crit * se)

    reject_null = bool(p_value < 0.05)

    return {
        "group_means": {"A": mean_a, "B": mean_b},
        "n": {"A": n_a, "B": n_b},
        "t_stat": t_stat,
        "p_value": p_value,
        "df": welch_df,
        "cohens_d": cohens_d,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": reject_null,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python solution.py --data <csv> --output-dir <dir>."""
    parser = argparse.ArgumentParser(description="A/B test statistical report")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write results.json
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    # Plot 1: histograms for each group
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, grp, color in zip(axes, ["A", "B"], ["steelblue", "darkorange"]):
        vals = df.loc[df["group"] == grp, "value"]
        ax.hist(vals, bins=20, color=color, edgecolor="black", alpha=0.7)
        ax.set_title(f"Group {grp} distribution")
        ax.set_xlabel("value")
        ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(str(out_dir / "histograms.png"), dpi=80)
    plt.close(fig)

    # Plot 2: boxplot comparing groups
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    data_by_group = [
        df.loc[df["group"] == "A", "value"].values,
        df.loc[df["group"] == "B", "value"].values,
    ]
    ax2.boxplot(data_by_group, labels=["A", "B"], patch_artist=True,
                boxprops=dict(facecolor="lightblue"))
    ax2.set_title("A/B Group Boxplot")
    ax2.set_xlabel("Group")
    ax2.set_ylabel("value")
    fig2.tight_layout()
    fig2.savefig(str(out_dir / "boxplot.png"), dpi=80)
    plt.close(fig2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
