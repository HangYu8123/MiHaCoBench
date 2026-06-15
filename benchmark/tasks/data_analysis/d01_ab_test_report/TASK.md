# Data Analysis 01 — `ab_test_report`: Two-Sample A/B Test Analysis

**Created:** 2026-06-15 · **Category:** data_analysis · **Weight:** 3

Analyse a pre-collected A/B experiment dataset stored at `data/ab_data.csv`
(committed in the task directory). The CSV has two columns:

| Column | Type | Values |
|--------|------|--------|
| `group` | str | `"A"` or `"B"` |
| `value` | float | continuous measurement |

Implement your solution in a single file `solution.py`.

## Public contract

### `analyze(df: pandas.DataFrame) -> dict`

Run a Welch two-sample t-test (`scipy.stats.ttest_ind` with
`equal_var=False`) comparing group B against group A (B minus A
orientation, so a positive `t_stat` means B > A).

Return a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `group_means` | `{"A": float, "B": float}` | Arithmetic mean of each group |
| `n` | `{"A": int, "B": int}` | Sample size of each group |
| `t_stat` | float | Welch t-statistic (B vs A, positive when B > A) |
| `p_value` | float | Two-tailed p-value from the test |
| `df` | float | Degrees of freedom (Welch–Satterthwaite) |
| `cohens_d` | float | Cohen's d effect size: `(mean_B - mean_A) / pooled_std` where `pooled_std = sqrt((std_A**2 + std_B**2) / 2)` using sample standard deviations (ddof=1) |
| `ci95_low` | float | Lower bound of 95% confidence interval of mean difference (B − A) |
| `ci95_high` | float | Upper bound of 95% confidence interval of mean difference (B − A) |
| `reject_null` | bool | `True` iff `p_value < 0.05` |

The 95% CI must be computed as:
```
diff = mean_B - mean_A
se = sqrt(std_A**2/n_A + std_B**2/n_B)   # using ddof=1 sample stds
t_crit = scipy.stats.t.ppf(0.975, df=welch_df)
ci95_low  = diff - t_crit * se
ci95_high = diff + t_crit * se
```

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze`, and writes two outputs
inside `<dir>`:

1. **`results.json`** — `json.dumps(analyze(df))` (all keys present).
2. **Two PNG files** (any filenames, ending in `.png`):
   - A histogram of `value` for each group (can be one figure with two
     subplots, or two separate files — the grader checks `count >= 2`).
   - A boxplot comparing the two groups.

Both figures must be saved as PNGs; no interactive display (`plt.show()` is
forbidden — set `matplotlib.use("Agg")` or rely on `MPLBACKEND=Agg`).

Exit code `0` on success, non-zero on error.

## Notes

* `scipy.stats.ttest_ind` must appear in your source (surface-form check).
* Seeds/determinism are not required for the analysis itself (the dataset is
  fixed), but keep side effects out of module-level scope.
* Do not modify the CSV file.
