# Data Analysis 02 — `sales_trend`: Monthly Sales Trend Analysis

**Created:** 2026-06-15 · **Category:** data_analysis · **Weight:** 3

Analyse a pre-collected monthly sales dataset stored at `data/sales.csv`
(committed in the task directory). The CSV has four columns:

| Column | Type | Description |
|--------|------|-------------|
| `month_index` | int | 0–47, sequential month number |
| `month_of_year` | int | 0–11, repeating (0 = January) |
| `units` | int | number of units sold |
| `price` | float | average unit price |

Implement your solution in a single file `solution.py`.

## Public contract

### `analyze(df: pandas.DataFrame) -> dict`

Perform three analyses on the dataframe and return a dict with **exactly**
these keys:

#### Linear trend of units over time

Fit a degree-1 polynomial to `units` (y) versus `month_index` (x) using
`numpy.polyfit(x, y, 1)` (or equivalently `sklearn.linear_model.LinearRegression`).

| Key | Type | Description |
|-----|------|-------------|
| `slope` | float | slope of the fitted line |
| `intercept` | float | intercept of the fitted line |
| `r_squared` | float | coefficient of determination R² = 1 − SS_res / SS_tot |
| `trend_direction` | str | `"up"` if slope > 0.1, `"down"` if slope < −0.1, else `"flat"` |

#### Seasonal ANOVA

Group `units` by `month_of_year` and perform a one-way ANOVA using
`scipy.stats.f_oneway(*groups)`.

| Key | Type | Description |
|-----|------|-------------|
| `anova_F` | float | F-statistic from `f_oneway` |
| `anova_p` | float | p-value from `f_oneway` |
| `seasonal_significant` | bool | `True` iff `anova_p < 0.05` |

#### Price–units correlation

Compute the Pearson correlation between `price` and `units` using
`scipy.stats.pearsonr(price, units)`.

| Key | Type | Description |
|-----|------|-------------|
| `pearson_price_units` | float | Pearson r (price correlated with units) |
| `pearson_p` | float | two-tailed p-value |

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze`, and writes to `<dir>`:

1. **`results.json`** — `json.dumps(analyze(df))` (all nine keys present).
2. **At least three PNG files** (any filenames ending in `.png`):
   - A scatter plot of `units` vs `month_index` with the trend line overlaid.
   - A bar chart of mean `units` per `month_of_year` (seasonal profile).
   - A scatter plot of `price` vs `units`.

Figures must be saved as PNGs; no interactive display (`MPLBACKEND=Agg` is
set by the test runner).

Exit code `0` on success, non-zero on error.

## Notes

* `f_oneway` and `pearsonr` **must** appear in your source (surface-form check).
* The dataset is fixed; do not modify `data/sales.csv`.
* Do not put side effects at module level.
