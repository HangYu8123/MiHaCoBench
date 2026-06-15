# Data Analysis 04 — `survey_correlation`: Categorical Dependence & Numeric Correlation

**Created:** 2026-06-15 · **Category:** data_analysis · **Weight:** 3

Analyse a pre-collected customer survey stored at `data/survey.csv` (committed
in the task directory).  The CSV has 500 rows and these columns:

| Column | Type | Values |
|--------|------|--------|
| `region` | str | `"N"`, `"S"`, `"E"`, `"W"` |
| `plan` | str | `"basic"`, `"pro"`, `"max"` |
| `age` | float | integer ages 18–65 |
| `income` | float | annual income in USD |
| `usage_hours` | float | weekly product usage hours |
| `satisfaction` | float | integer satisfaction score 1–10 |

Implement your solution in a single file `solution.py`.

## Public contract

### `analyze(df: pandas.DataFrame) -> dict`

Perform two analyses:

**1. Chi-square test of independence** on the contingency table of `region × plan`:
- Use `scipy.stats.chi2_contingency` with default parameters on
  `pandas.crosstab(df["region"], df["plan"])`.

**2. Pearson correlation** among the four numeric columns
(`age`, `income`, `usage_hours`, `satisfaction`):
- Compute the correlation matrix using `pandas.DataFrame.corr()` (default
  Pearson method) on just those four columns.
- Find the pair of columns with the **highest absolute Pearson r** among all
  unique pairs (i.e., ignore the diagonal and each pair appears once).
- If two pairs tie on absolute value, break the tie by choosing the pair whose
  first column name comes first alphabetically, then by second column name.

Return a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `chi2` | float | Chi-square statistic from `chi2_contingency` |
| `chi2_p` | float | p-value from `chi2_contingency` |
| `dof` | int | Degrees of freedom from `chi2_contingency` (for 4×3 table: 6) |
| `dependent` | bool | `True` iff `chi2_p < 0.05` (reject independence) |
| `corr_strongest_pair` | list[str] | The two column names with highest absolute r, **sorted alphabetically** |
| `corr_strongest_r` | float | The Pearson r value for that pair (signed, not absolute) |

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze`, and writes these outputs
inside `<dir>`:

1. **`results.json`** — `json.dumps(analyze(df))` (all keys present).
2. **At least 2 PNG files** (any filenames ending in `.png`):
   - A heatmap of the numeric correlation matrix (the 4×4 Pearson r grid).
   - A grouped bar chart (or stacked bar chart) visualising the `region × plan`
     crosstab counts.

Both figures must be saved as PNGs; no interactive display (`plt.show()` is
forbidden — set `matplotlib.use("Agg")` or rely on `MPLBACKEND=Agg`).

Exit code `0` on success, non-zero on error.

## Notes

* `scipy.stats.chi2_contingency` must appear in your source (surface-form check).
* The dataset is fixed (seeded RNG=11, n=500). Do not modify the CSV file.
* `corr_strongest_pair` must be a Python `list` with the two names in
  ascending alphabetical order (e.g., `["income", "usage_hours"]`).
* `dof` must be an `int` (not a float).
