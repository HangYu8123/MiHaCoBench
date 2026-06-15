"""solution.py — A/B test analysis for d01_ab_test_report.

Public API
----------
analyze(df)      -> dict   : Run Welch t-test and return statistics.
main(argv=None)  -> int    : CLI entry point; writes results.json and PNGs.
"""

import matplotlib
matplotlib.use("Agg")  # Must be called before importing pyplot
import matplotlib.pyplot as plt

import sys
import os
import json
import argparse

import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Run a Welch two-sample t-test comparing group B against group A.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'group' (str: "A"/"B") and 'value' (float).

    Returns
    -------
    dict with keys:
        group_means : dict {"A": float, "B": float}
        n           : dict {"A": int, "B": int}
        t_stat      : float  — Welch t-statistic (B vs A; positive when B > A)
        p_value     : float  — two-tailed p-value
        df          : float  — Welch-Satterthwaite degrees of freedom
        cohens_d    : float  — Cohen's d effect size
        ci95_low    : float  — lower bound of 95% CI of mean difference (B - A)
        ci95_high   : float  — upper bound of 95% CI of mean difference (B - A)
        reject_null : bool   — True iff p_value < 0.05
    """
    # 1. Split into numpy arrays
    a = df[df["group"] == "A"]["value"].to_numpy(dtype=float)
    b = df[df["group"] == "B"]["value"].to_numpy(dtype=float)

    # 2. Group means
    mean_A = float(a.mean())
    mean_B = float(b.mean())

    # 3. Sample sizes
    n_A = int(len(a))
    n_B = int(len(b))

    # 4. Sample standard deviations (ddof=1)
    std_A = float(a.std(ddof=1))
    std_B = float(b.std(ddof=1))

    # 5. Welch t-test — B first so positive t_stat means B > A
    result = scipy.stats.ttest_ind(b, a, equal_var=False)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)

    # 6. Welch-Satterthwaite degrees of freedom
    #    result.df was added in scipy 1.11.0; fall back to manual formula
    try:
        welch_df = float(result.df)
    except AttributeError:
        num = (std_A ** 2 / n_A + std_B ** 2 / n_B) ** 2
        denom = (
            (std_A ** 2 / n_A) ** 2 / (n_A - 1)
            + (std_B ** 2 / n_B) ** 2 / (n_B - 1)
        )
        welch_df = float(num / denom)

    # 7. Cohen's d (equal-weight pooled std, NOT n-weighted)
    pooled_std = float(np.sqrt((std_A ** 2 + std_B ** 2) / 2.0))
    cohens_d = float((mean_B - mean_A) / pooled_std)

    # 8. 95% CI of the mean difference (B − A)
    diff = mean_B - mean_A
    se = float(np.sqrt(std_A ** 2 / n_A + std_B ** 2 / n_B))
    t_crit = float(scipy.stats.t.ppf(0.975, df=welch_df))
    ci95_low = float(diff - t_crit * se)
    ci95_high = float(diff + t_crit * se)

    # 9. Null rejection
    reject_null = bool(p_value < 0.05)

    return {
        "group_means": {"A": mean_A, "B": mean_B},
        "n":           {"A": n_A,    "B": n_B},
        "t_stat":      t_stat,
        "p_value":     p_value,
        "df":          welch_df,
        "cohens_d":    cohens_d,
        "ci95_low":    ci95_low,
        "ci95_high":   ci95_high,
        "reject_null": reject_null,
    }


def main(argv=None):
    """CLI entry point.

    Usage
    -----
    python solution.py --data <csv_path> --output-dir <dir>

    Parameters
    ----------
    argv : list[str] | None
        Argument list (excluding the script name). When None, sys.argv[1:]
        is used automatically by argparse.

    Returns
    -------
    int
        0 on success, 1 on any error.
    """
    parser = argparse.ArgumentParser(
        description="Run A/B test analysis and write results to an output directory."
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to the input CSV file (must have 'group' and 'value' columns).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        dest="output_dir",
        help="Directory where results.json and PNG plots will be written.",
    )

    args = parser.parse_args(argv)

    try:
        # Read input
        df = pd.read_csv(args.data)

        # Create output directory (may not exist yet)
        os.makedirs(args.output_dir, exist_ok=True)

        # Run analysis and write JSON
        results = analyze(df)
        results_path = os.path.join(args.output_dir, "results.json")
        with open(results_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh)

        # Re-extract group arrays for plotting
        a_vals = df[df["group"] == "A"]["value"].to_numpy(dtype=float)
        b_vals = df[df["group"] == "B"]["value"].to_numpy(dtype=float)

        # --- Plot 1: Histograms (one figure, two subplots) ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        ax1.hist(a_vals, color="steelblue", edgecolor="white")
        ax1.set_title("Group A")
        ax1.set_xlabel("value")
        ax1.set_ylabel("count")
        ax2.hist(b_vals, color="darkorange", edgecolor="white")
        ax2.set_title("Group B")
        ax2.set_xlabel("value")
        ax2.set_ylabel("count")
        fig.suptitle("Value Distribution by Group")
        fig.tight_layout()
        fig.savefig(os.path.join(args.output_dir, "histograms.png"), dpi=100)
        plt.close(fig)

        # --- Plot 2: Boxplot ---
        fig, ax = plt.subplots(figsize=(6, 5))
        # Use tick_labels (matplotlib >= 3.9); fall back to labels for older versions
        _mpl_version = tuple(
            int(x) for x in matplotlib.__version__.split(".")[:2]
        )
        if _mpl_version >= (3, 9):
            ax.boxplot([a_vals, b_vals], tick_labels=["A", "B"])
        else:
            ax.boxplot([a_vals, b_vals], labels=["A", "B"])
        ax.set_title("Boxplot by Group")
        ax.set_xlabel("group")
        ax.set_ylabel("value")
        fig.tight_layout()
        fig.savefig(os.path.join(args.output_dir, "boxplot.png"), dpi=100)
        plt.close(fig)

    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
