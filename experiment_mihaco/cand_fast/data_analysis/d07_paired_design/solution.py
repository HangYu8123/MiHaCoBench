"""
d07_paired_design — Paired Before/After Experiment Report
Implements analyze() and main() for paired t-test analysis.
"""

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats


def analyze(df: pd.DataFrame) -> dict:
    """
    Run a paired t-test comparing after vs before using scipy.stats.ttest_rel(after, before).
    Returns a dict with exactly the keys specified in the contract.
    """
    n = int(len(df))
    diffs = df['after'] - df['before']

    mean_before = float(df['before'].mean())
    mean_after = float(df['after'].mean())
    mean_diff = float(diffs.mean())

    std_diff = float(diffs.std(ddof=1))
    se = std_diff / np.sqrt(n)

    t_stat, p_value = scipy.stats.ttest_rel(df['after'], df['before'])
    t_stat = float(t_stat)
    p_value = float(p_value)

    cohens_d = mean_diff / std_diff

    t_crit = scipy.stats.t.ppf(0.975, df=n - 1)
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
        'cohens_d': float(cohens_d),
        'ci95_low': ci95_low,
        'ci95_high': ci95_high,
        'reject_null': reject_null,
    }


def main(argv=None) -> int:
    """
    CLI entry point.
    Usage: python solution.py --data <csv_path> --output-dir <dir>
    """
    try:
        parser = argparse.ArgumentParser(description='Paired before/after experiment analysis')
        parser.add_argument('--data', required=True, help='Path to paired CSV file')
        parser.add_argument('--output-dir', required=True, help='Directory for output files')
        args = parser.parse_args(argv)

        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        df = pd.read_csv(args.data)
        result = analyze(df)

        # Write results.json
        results_path = os.path.join(output_dir, 'results.json')
        with open(results_path, 'w') as f:
            json.dump(result, f, indent=2)

        diffs = df['after'] - df['before']

        # Plot 1: Histogram of paired differences
        fig, ax = plt.subplots()
        ax.hist(diffs, bins='auto', edgecolor='black')
        ax.set_xlabel('Paired Difference (after - before)')
        ax.set_ylabel('Count')
        ax.set_title('Histogram of Paired Differences')
        ax.axvline(x=0, color='red', linestyle='--', label='Zero')
        ax.legend()
        plt.savefig(os.path.join(output_dir, 'diffs_histogram.png'))
        plt.close()

        # Plot 2: Before-vs-after paired plot (one line per subject)
        fig, ax = plt.subplots()
        x_before = 0
        x_after = 1
        for i, row in df.iterrows():
            ax.plot([x_before, x_after], [row['before'], row['after']],
                    color='steelblue', alpha=0.4, linewidth=0.8)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['Before', 'After'])
        ax.set_ylabel('Measurement')
        ax.set_title('Paired Before/After Plot')
        plt.savefig(os.path.join(output_dir, 'paired_plot.png'))
        plt.close()

        return 0

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
