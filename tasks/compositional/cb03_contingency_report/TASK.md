# Compositional 03 — `cb03_contingency_report`: Survey Contingency Analysis

**Created:** 2026-06-15 · **Category:** compositional · **Weight:** 4

You are given a CSV file (`data/survey.csv`) with two columns:

| Column     | Type  | Values                       |
|------------|-------|------------------------------|
| `group`    | `str` | `"control"` or `"treatment"` |
| `response` | `str` | `"yes"`, `"no"`, or `"maybe"` |

Write **`solution.py`** with one public function:

```python
def analyze(df: pandas.DataFrame) -> dict:
    ...
```

## What `analyze` must do

1. **Contingency table** — build a cross-tabulation of `group` × `response`
   using `pandas.crosstab`.  The result should count occurrences of each
   `(group, response)` pair.

2. **Chi-squared test** — run `scipy.stats.chi2_contingency` on the table
   (no continuity correction; `correction=False`).

3. **Cramér's V effect size**:

   ```
   V = sqrt(chi2 / (n * (min(r, c) - 1)))
   ```

   where `n` is the total number of observations, `r` is the number of rows
   (groups), and `c` is the number of columns (responses).

4. **Bootstrap 95 % CI for the yes-rate difference** (treatment − control):
   - Use `numpy` with a **fixed seed of `42`** set at the start of the
     bootstrap loop.
   - Draw **at least 1 000 resamples** (the grader uses exactly 1 000).
   - Each resample: sample with replacement within each group; compute
     `yes_rate_treatment − yes_rate_control`.
   - The CI is the 2.5th and 97.5th percentiles of the bootstrap distribution.

## Return value

Return a **`dict`** with **exactly** these keys:

| Key          | Type    | Description                                                 |
|--------------|---------|-------------------------------------------------------------|
| `table`      | `dict`  | Nested dict: `table[group][response] = count (int)`.        |
|              |         | Outer keys: `"control"`, `"treatment"`.                     |
|              |         | Inner keys: `"yes"`, `"no"`, `"maybe"`.                     |
| `chi2`       | `float` | Chi-squared statistic from `scipy.stats.chi2_contingency`.  |
| `dof`        | `int`   | Degrees of freedom (integer).                               |
| `p_value`    | `float` | p-value from the chi-squared test.                          |
| `cramers_v`  | `float` | Cramér's V effect size (non-negative).                      |
| `ci95_low`   | `float` | Lower bound of the 95 % bootstrap CI.                       |
| `ci95_high`  | `float` | Upper bound of the 95 % bootstrap CI.                       |
| `reject_null`| `bool`  | `True` if and only if `p_value < 0.05`.                     |

### `table` structure example

```python
{
    "control":   {"yes": 40, "no": 35, "maybe": 25},
    "treatment": {"yes": 60, "no": 20, "maybe": 20}
}
```

All counts are plain Python `int` values.

## Error handling

If `df` is missing the `"group"` or `"response"` column, raise `KeyError` or
`ValueError`.

## Notes

- The grader checks `table` values for exact integer equality.
- `chi2` and `cramers_v` are compared with `rtol=1e-3`.
- `dof` is checked as an exact integer.
- `reject_null` is checked as a boolean derived from `p_value < 0.05`; the
  raw `p_value` is not compared precisely (library versions may drift).
- CI bounds are compared with a generous tolerance (`rtol=0.05`).
- The dataset has a **genuine significant association** between group and
  response, so `reject_null` should be `True`.
- You must use `scipy.stats.chi2_contingency` (the grader checks via
  `source_uses`).
