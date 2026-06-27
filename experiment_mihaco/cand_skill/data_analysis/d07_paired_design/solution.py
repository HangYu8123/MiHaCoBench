import matplotlib
matplotlib.use("Agg")

import argparse
import json
import math
import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Run a paired t-test comparing after against before.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain 'before' and 'after' columns.

    Returns
    -------
    dict with exactly 10 keys.
    """
    n = len(df)
    diffs = df["after"] - df["before"]

    t_stat, p_value = scipy.stats.ttest_rel(df["after"], df["before"])

    mean_before = df["before"].mean()
    mean_after = df["after"].mean()
    mean_diff = diffs.mean()
    std_diff = diffs.std(ddof=1)

    cohens_d = mean_diff / std_diff

    se = std_diff / math.sqrt(n)
    t_crit = scipy.stats.t.ppf(0.975, df=n - 1)
    ci95_low = mean_diff - t_crit * se
    ci95_high = mean_diff + t_crit * se

    reject_null = bool(p_value < 0.05)

    return {
        "n": int(n),
        "mean_before": float(mean_before),
        "mean_after": float(mean_after),
        "mean_diff": float(mean_diff),
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "cohens_d": float(cohens_d),
        "ci95_low": float(ci95_low),
        "ci95_high": float(ci95_high),
        "reject_null": reject_null,
    }


def main(argv=None) -> int:
    """CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>
    """
    parser = argparse.ArgumentParser(
        description="Paired before/after experiment analysis"
    )
    parser.add_argument("--data", required=True, help="Path to paired.csv")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)

    try:
        output_dir = pathlib.Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_csv(args.data)
        results = analyze(df)

        # Write results.json
        results_path = output_dir / "results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)

        diffs = df["after"] - df["before"]

        # Plot 1: Histogram of paired differences
        fig, ax = plt.subplots()
        ax.hist(diffs, bins="auto", color="steelblue", edgecolor="black")
        ax.set_xlabel("Paired Difference (after - before)")
        ax.set_ylabel("Count")
        ax.set_title("Histogram of Paired Differences")
        fig.savefig(output_dir / "diff_histogram.png")
        plt.close(fig)

        # Plot 2: Before-vs-after paired plot
        fig, ax = plt.subplots()
        for _, row in df.iterrows():
            ax.plot([0, 1], [row["before"], row["after"]], color="steelblue", alpha=0.5)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Before", "After"])
        ax.set_ylabel("Measurement")
        ax.set_title("Paired Before vs. After Plot")
        fig.savefig(output_dir / "paired_plot.png")
        plt.close(fig)

        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
