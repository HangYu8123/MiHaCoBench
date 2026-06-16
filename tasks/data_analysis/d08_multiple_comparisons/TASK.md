# Data Analysis 08 — `multiple_comparisons`: K-Group Comparison with Family-Wise Error Control

**Created:** 2026-06-16 · **Category:** data_analysis · **Weight:** 3

Analyse a pre-collected K-group experiment dataset stored at `data/groups.csv`
(committed in the task directory). The CSV has two columns:

| Column | Type | Values |
|--------|------|--------|
| `group` | str | one of `"A"`, `"B"`, `"C"`, `"D"` |
| `value` | float | continuous measurement |

There are 35 rows per group (140 total). Implement your solution in a single
file `solution.py`.

## The twist

Running an independent-samples t-test on **every** pair of groups inflates the
family-wise error rate: with K=4 groups there are C(4,2)=6 comparisons, so the
naive procedure over-rejects. The contract requires you to (a) run an omnibus
ANOVA first, and (b) control the family-wise error rate of the pairwise tests
with the **Holm-Bonferroni step-down** procedure. A pair that is significant
under a raw pairwise t-test may **not** survive the correction — that is the
intended behaviour, not a bug.

## Public contract

### `analyze(df: pandas.DataFrame) -> dict`

1. **Omnibus test.** Compute a one-way ANOVA across all groups using
   `scipy.stats.f_oneway` (one positional array per group).
2. **Pairwise tests.** For every unordered pair of distinct group labels, in
   **sorted label order**, run an independent two-sample t-test with
   `scipy.stats.ttest_ind(..., equal_var=True)` (Student's t-test, equal
   variances assumed). The pair key is `"X_vs_Y"` where `X < Y` lexicographically
   (e.g. `"A_vs_B"`, `"A_vs_C"`, ..., `"C_vs_D"`).
3. **Correction.** Adjust the 6 raw pairwise p-values with the **Holm-Bonferroni
   step-down** procedure at family-wise error rate `alpha = 0.05`:
   sort the raw p-values ascending; the k-th smallest (k = 0, 1, ...) is
   multiplied by `(m - k)` where `m` is the number of comparisons; enforce
   monotonicity (each adjusted p is at least the previous one) and cap at `1.0`.
   A pair is **significant** iff its **Holm-adjusted** p-value `< 0.05`.

Return a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `group_means` | `{label: float}` | Arithmetic mean of `value` per group |
| `n_per_group` | `{label: int}` | Sample size per group |
| `anova_f` | float | One-way ANOVA F-statistic from `scipy.stats.f_oneway` |
| `anova_p` | float | One-way ANOVA p-value |
| `omnibus_significant` | bool | `True` iff `anova_p < 0.05` |
| `pairs` | `{"X_vs_Y": {...}}` | One entry per C(K,2) pair (sorted label order); see below |
| `n_significant_pairs` | int | Count of pairs whose Holm-adjusted p < 0.05 |

Each `pairs["X_vs_Y"]` value is a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `raw_p` | float | Raw two-tailed p-value from `ttest_ind` (no correction) |
| `adj_p` | float | Holm-Bonferroni adjusted p-value (`>= raw_p`) |
| `significant` | bool | `True` iff `adj_p < 0.05` |

Notes:

* `group_means` and `n_per_group` must be keyed by the actual group labels.
* `scipy.stats.f_oneway` must appear in your source (surface-form check).
* `adj_p` must be `>= raw_p` for every pair (a correction never makes a p-value
  smaller).

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze`, and writes inside `<dir>`:

1. **`results.json`** — `json.dumps(analyze(df))` (all keys above present).
2. **Two PNG files** (any filenames ending in `.png`; the grader checks
   `count >= 2`):
   - A bar chart of group means with error bars.
   - A pairwise adjusted-p heatmap / matrix.

Both figures must be saved as PNGs; no interactive display (`plt.show()` is
forbidden — set `matplotlib.use("Agg")` or rely on `MPLBACKEND=Agg`).

Exit code `0` on success, non-zero on error.

## Notes

* Seeds/determinism are not required for the analysis itself (the dataset is
  fixed), but keep side effects out of module-level scope.
* Do not modify the CSV file.
