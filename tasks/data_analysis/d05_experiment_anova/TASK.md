# Data Analysis 05 — `experiment_anova`: One-Way ANOVA with Bonferroni Correction

**Created:** 2026-06-15 · **Category:** data_analysis · **Weight:** 3

You are given a CSV file (`data/experiment.csv`) with two columns:

| Column | Description |
|---|---|
| `group` | Categorical label: one of `"ctrl"`, `"low"`, or `"high"` |
| `response` | Continuous numeric measurement (float) |

There are 150 observations per group (450 rows total).

## Task

Write `solution.py` with:

1. **`analyze(df: pd.DataFrame) -> dict`** — performs a one-way ANOVA and pairwise
   t-tests with Bonferroni correction on the data. Returns a dict with **exactly**
   these keys:

   | Key | Type | Description |
   |---|---|---|
   | `group_means` | `dict[str, float]` | Mean `response` per group, e.g. `{"ctrl": ..., "low": ..., "high": ...}` |
   | `anova_F` | `float` | F-statistic from one-way ANOVA (`scipy.stats.f_oneway`) |
   | `anova_p` | `float` | p-value from one-way ANOVA |
   | `significant` | `bool` | `True` iff `anova_p < 0.05` |
   | `significant_pairs` | `list[list[str]]` | Pairs of groups that differ significantly after Bonferroni correction |

   **Bonferroni procedure for `significant_pairs`:**
   - Run `scipy.stats.ttest_ind` for each of the 3 pairwise combinations:
     `(ctrl, low)`, `(ctrl, high)`, `(low, high)`.
   - The number of comparisons is **3** (fixed).
   - Corrected p-value = `min(raw_p * 3, 1.0)`.
   - A pair is included iff `corrected_p < 0.05`.
   - Each pair is a 2-element list sorted alphabetically, e.g. `["ctrl", "high"]`.
   - The returned list is sorted (lexicographically by first element, then second).

2. **`main(argv: list[str] | None = None)`** — CLI entry point using `argparse`:

   ```
   python solution.py --data <path_to_csv> --output-dir <dir>
   ```

   Reads the CSV with `pandas.read_csv`, calls `analyze(df)`, and writes:

   - `<output-dir>/results.json` — the dict returned by `analyze` serialised with
     `json.dump` (default Python JSON encoding; no special formatting required).
   - `<output-dir>/boxplot.png` — a box plot with one box per group.
   - `<output-dir>/errorbar.png` — a mean ± 95 % CI error-bar chart with one point
     per group.

   Both plots must be saved with `matplotlib` and use the `Agg` backend (non-interactive).
   Exit with status `0` on success.

   Both PNGs must be valid image files with real visual content.

## Notes

- Use `scipy.stats.f_oneway` for the ANOVA (the grader checks via `source_uses`).
- Use `scipy.stats.ttest_ind` for pairwise tests (also checked via `source_uses`).
- Do **not** use any multiple-comparison library (e.g. `statsmodels`); implement
  Bonferroni by hand as described above.
- Floats are compared with relative tolerance `rtol=1e-3` by the grader.
- The 95 % CI half-width for group `g` is `1.96 * std(g) / sqrt(n_g)`.
