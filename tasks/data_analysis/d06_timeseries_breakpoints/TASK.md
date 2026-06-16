# Data Analysis 06 — `d06_timeseries_breakpoints`: Time-Series Changepoint Detection

**Created:** 2026-06-15 · **Category:** data_analysis · **Weight:** 3

Analyse a pre-collected time-series dataset stored at `data/series.csv`
(committed in the task directory). The CSV has two columns:

| Column | Type | Description |
|--------|------|-------------|
| `day`  | int  | 0–N-1, sequential day index |
| `value` | float | observed value; the series has one clear level shift |

Implement your solution in a single file `solution.py`.

## Public contract

### `analyze(df: pandas.DataFrame) -> dict`

Perform the following analyses on the dataframe and return a dict with **exactly**
these keys:

#### 7-day Rolling statistics

Compute a 7-day rolling mean and rolling standard deviation using
`pandas.DataFrame.rolling(window=7)`.

| Key | Type | Description |
|-----|------|-------------|
| `rolling_mean_last` | float | rolling mean value at the last row (`.iloc[-1]`) |

#### Changepoint detection

Detect the single largest changepoint as the index `i` (in range `[1, len(df)-1)`)
that maximises `abs(mean(values[:i]) - mean(values[i:]))`.

| Key | Type | Description |
|-----|------|-------------|
| `breakpoint_index` | int | 0-based row index of the detected changepoint |
| `mean_before` | float | mean of `value` for rows with index < `breakpoint_index` |
| `mean_after` | float | mean of `value` for rows with index >= `breakpoint_index` |

#### Welch t-test

Run a Welch two-sample t-test (unequal variances) using
`scipy.stats.ttest_ind(before, after, equal_var=False)`
comparing values before vs. after the detected breakpoint.

| Key | Type | Description |
|-----|------|-------------|
| `t_stat` | float | t-statistic from `ttest_ind` |
| `p_value` | float | two-tailed p-value from `ttest_ind` |
| `reject_null` | bool | `True` iff `p_value < 0.05` |

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze`, and writes to `<dir>`:

1. **`results.json`** — `json.dumps(analyze(df))` (all seven keys present).
2. **`series.png`** — a line plot of `value` over `day` with a vertical line
   marking the detected `breakpoint_index`.

The figure must be saved as a PNG; no interactive display (`MPLBACKEND=Agg` is
set by the test runner).

Exit code `0` on success, non-zero on error.

### Exception contract

Calling `analyze` with an **empty** DataFrame (zero rows) must raise `ValueError`.

## Notes

* `rolling` (from `pandas.DataFrame.rolling`) **must** appear in your source.
* `ttest_ind` (from `scipy.stats`) **must** appear in your source.
* The dataset is fixed; do not modify `data/series.csv`.
* Do not put side effects at module level.
