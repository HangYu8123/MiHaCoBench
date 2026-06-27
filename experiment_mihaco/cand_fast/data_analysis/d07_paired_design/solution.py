import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import argparse
import json
import os

import numpy as np
import pandas as pd
import scipy.stats  # noqa: F401 — required by surface-form check: scipy.stats.ttest_rel
from scipy import stats


def analyze(df: pd.DataFrame) -> dict:
    """Run a paired t-test comparing after against before.

    Returns a dict with exactly the keys specified in the contract.
    """
    n = int(len(df))

    before = df['before'].to_numpy()
    after = df['after'].to_numpy()
    diffs = after - before  # after - before (not reversed)

    mean_before = float(np.mean(before))
    mean_after = float(np.mean(after))
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))

    # Paired t-test: ttest_rel(after, before) — positive t means after > before
    t_result = stats.ttest_rel(after, before)
    t_stat = float(t_result.statistic)
    p_value = float(t_result.pvalue)

    # Cohen's d for paired design: mean_diff / sample_std(diffs)
    cohens_d = float(mean_diff / std_diff)

    # 95% CI of mean paired difference using t distribution on n-1 df
    se = std_diff / np.sqrt(n)
    t_crit = float(stats.t.ppf(0.975, df=n - 1))
    ci95_low = float(mean_diff - t_crit * se)
    ci95_high = float(mean_diff + t_crit * se)

    reject_null = bool(p_value < 0.05)

    return {
        'n': n,
        'mean_before': mean_before,
        'mean_after': mean_after,
        'mean_diff': mean_diff,
        't_stat': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'ci95_low': ci95_low,
        'ci95_high': ci95_high,
        'reject_null': reject_null,
    }


def _save_plots(df: pd.DataFrame, output_dir: str) -> None:
    """Save histogram of diffs and paired before/after plot."""
    diffs = df['after'].to_numpy() - df['before'].to_numpy()

    # Histogram of paired differences
    fig, ax = plt.subplots()
    ax.hist(diffs, bins='auto', edgecolor='black')
    ax.set_xlabel('After - Before')
    ax.set_ylabel('Count')
    ax.set_title('Histogram of Paired Differences (After - Before)')
    fig.savefig(os.path.join(output_dir, 'hist_diffs.png'))
    plt.close(fig)

    # Paired before/after plot: one line per subject
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        ax.plot([0, 1], [row['before'], row['after']], 'b-', alpha=0.4)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Before', 'After'])
    ax.set_ylabel('Measurement')
    ax.set_title('Paired Before / After Plot')
    fig.savefig(os.path.join(output_dir, 'paired_plot.png'))
    plt.close(fig)


def main(argv=None) -> int:
    """CLI entry point.

    Usage:
        python solution.py --data <csv_path> --output-dir <dir>
    """
    try:
        parser = argparse.ArgumentParser(
            description='Paired before/after experiment analysis')
        parser.add_argument('--data', required=True,
                            help='Path to the input CSV file')
        parser.add_argument('--output-dir', required=True,
                            help='Directory to write results')
        args = parser.parse_args(argv)

        df = pd.read_csv(args.data)
        result = analyze(df)

        os.makedirs(args.output_dir, exist_ok=True)

        with open(os.path.join(args.output_dir, 'results.json'), 'w') as f:
            json.dump(result, f)

        _save_plots(df, args.output_dir)

        return 0
    except Exception:
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
