"""Deliberately-broken reference for data_analysis/d07_paired_design.

Planted defect:
  The data is a *paired* before/after design, but this solution runs the
  UNPAIRED two-sample test ``scipy.stats.ttest_ind(after, before)`` instead of
  the paired ``scipy.stats.ttest_rel(after, before)``. The unpaired test ignores
  the pairing and is badly underpowered when between-subject variance dominates
  the within-subject effect, so:
    * ``t_stat`` and ``p_value`` differ from the paired reference, and
    * the surface-form constraint (ttest_rel present, ttest_ind absent) fails.

The mean/n keys are still computed correctly (so those tests still pass — they
are the PASS_TO_PASS anchors). The solution imports and runs cleanly; it is a
logic bug, not a crash.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """Run a t-test on the before/after dataset — BROKEN: uses the unpaired test."""
    before = df["before"].to_numpy(dtype=float)
    after = df["after"].to_numpy(dtype=float)

    n = int(len(df))
    mean_before = float(np.mean(before))
    mean_after = float(np.mean(after))

    diffs = after - before
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))

    # BUG: independent two-sample test on a paired design. Ignores the pairing,
    # so t_stat / p_value are wrong (underpowered) for this experiment.
    t_stat, p_value = scipy.stats.ttest_ind(after, before)
    t_stat = float(t_stat)
    p_value = float(p_value)

    cohens_d = float(mean_diff / std_diff)

    se = std_diff / math.sqrt(n)
    t_crit = float(scipy.stats.t.ppf(0.975, df=n - 1))
    ci95_low = float(mean_diff - t_crit * se)
    ci95_high = float(mean_diff + t_crit * se)

    reject_null = bool(p_value < 0.05)

    return {
        "n": n,
        "mean_before": mean_before,
        "mean_after": mean_after,
        "mean_diff": mean_diff,
        "t_stat": t_stat,
        "p_value": p_value,
        "cohens_d": cohens_d,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "reject_null": reject_null,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python solution.py --data <csv> --output-dir <dir>."""
    parser = argparse.ArgumentParser(description="Paired before/after experiment report")
    parser.add_argument("--data", required=True, help="Path to the CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.data)
    results = analyze(df)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "results.json").write_text(json.dumps(results, indent=2))

    before = df["before"].to_numpy(dtype=float)
    after = df["after"].to_numpy(dtype=float)
    diffs = after - before

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(diffs, bins=15, color="steelblue", edgecolor="black", alpha=0.8)
    ax.axvline(0.0, color="red", linestyle="--", linewidth=1.5, label="no change")
    ax.axvline(float(np.mean(diffs)), color="darkgreen", linewidth=1.5, label="mean diff")
    ax.set_title("Paired differences (after - before)")
    ax.set_xlabel("after - before")
    ax.set_ylabel("count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(str(out_dir / "differences_hist.png"), dpi=80)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(6, 5))
    for b, a in zip(before, after):
        ax2.plot([0, 1], [b, a], color="gray", alpha=0.5, linewidth=0.8)
    ax2.scatter(np.zeros_like(before), before, color="steelblue", zorder=3, label="before")
    ax2.scatter(np.ones_like(after), after, color="darkorange", zorder=3, label="after")
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(["before", "after"])
    ax2.set_xlim(-0.3, 1.3)
    ax2.set_ylabel("measurement")
    ax2.set_title("Paired before-vs-after")
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig(str(out_dir / "paired_plot.png"), dpi=80)
    plt.close(fig2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
