# Data Analysis 07 — `paired_design`: Paired Before/After Experiment Report

**Created:** 2026-06-16 · **Category:** data_analysis · **Weight:** 3

Analyse a pre-collected **paired** before/after experiment stored at
`data/paired.csv` (committed in the task directory). Each row is **one subject**
measured **twice** — once before the treatment and once after:

| Column | Type | Description |
|--------|------|-------------|
| `subject_id` | int | Unique subject identifier |
| `before` | float | Measurement before the treatment |
| `after` | float | Measurement after the treatment |

> **Read carefully — this is the trap.** Because the same subject appears in
> both columns, the two columns are **paired**, not independent. The correct
> test is the **paired** t-test `scipy.stats.ttest_rel(after, before)`. The
> obvious unpaired two-sample test (`scipy.stats.ttest_ind`) is **WRONG** here:
> the between-subject variance is large relative to the within-subject treatment
> effect, so the unpaired test is badly underpowered and reaches the opposite
> conclusion. **You must use the paired test.**

Implement your solution in a single file `solution.py`.

## Public contract

### `analyze(df: pandas.DataFrame) -> dict`

Run a **paired** t-test comparing `after` against `before` using
`scipy.stats.ttest_rel(after, before)` (this orientation makes a positive
`t_stat` mean `after > before`).

Let `diffs = after - before` (the per-subject paired differences).

Return a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `n` | int | Number of subjects (rows) |
| `mean_before` | float | Arithmetic mean of the `before` column |
| `mean_after` | float | Arithmetic mean of the `after` column |
| `mean_diff` | float | `mean(after - before)` |
| `t_stat` | float | Paired t-statistic from `scipy.stats.ttest_rel(after, before)` |
| `p_value` | float | Two-tailed p-value from the paired test |
| `cohens_d` | float | Paired effect size: `mean_diff / std(diffs, ddof=1)` |
| `ci95_low` | float | Lower bound of the 95% CI of the mean paired difference |
| `ci95_high` | float | Upper bound of the 95% CI of the mean paired difference |
| `reject_null` | bool | `True` iff `p_value < 0.05` |

The 95% CI of the mean paired difference must be computed with the t
distribution on `n - 1` degrees of freedom:

```
mean_diff = mean(diffs)
std_diff  = std(diffs, ddof=1)
se        = std_diff / sqrt(n)
t_crit    = scipy.stats.t.ppf(0.975, df=n - 1)
ci95_low  = mean_diff - t_crit * se
ci95_high = mean_diff + t_crit * se
```

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze`, and writes the following
inside `<dir>`:

1. **`results.json`** — `json.dumps(analyze(df))` (all keys above present).
2. **Two PNG files** (any filenames, ending in `.png`):
   - A **histogram of the paired differences** (`after - before`).
   - A **before-vs-after paired plot** (e.g. one connecting line per subject
     from its `before` value to its `after` value).

Both figures must be saved as PNGs; no interactive display (`plt.show()` is
forbidden — set `matplotlib.use("Agg")` or rely on `MPLBACKEND=Agg`).

Exit code `0` on success, non-zero on error.

## Notes

* **Surface-form constraints (enforced):** `scipy.stats.ttest_rel` **must**
  appear in your source, and `scipy.stats.ttest_ind` **must NOT** appear.
* Seeds/determinism are not required for the analysis itself (the dataset is
  fixed and committed), but keep side effects out of module-level scope.
* Do not modify the CSV file.
