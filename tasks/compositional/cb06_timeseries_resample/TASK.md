# Compositional 06 — `timeseries_resample`: Irregular Time-Series Resampling + Robust Outliers

**Created:** 2026-06-16 · **Category:** compositional · **Weight:** 4

You receive a list of irregularly-spaced sensor readings and must resample them
onto a regular grid, fill interior gaps, and flag outliers — composing **pandas**
(datetime index + resample), **numpy** (NaN-aware statistics), and **scipy**
(robust z-scores). The trap is correct NaN-handling: buckets that legitimately
stay empty must not poison the statistics.

Implement your solution in a single file `solution.py`.

## Public contract

### `resample_clean(readings: list[dict], freq: str) -> dict`

Each element of `readings` is a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `ts` | str | An ISO-8601 timestamp, e.g. `"2026-01-01T00:01:30"` |
| `value` | float | The reading. May be `NaN` (a sensor that reported a timestamp but no usable value). |

Perform the following steps, **in order**:

1. Parse every `ts` into a `pandas.DatetimeIndex`.
2. Sort the readings ascending by timestamp.
3. Drop duplicate timestamps, **keeping the LAST** occurrence of each.
4. Build a `pandas.Series` of `value` indexed by the timestamps.
5. Resample to `freq` taking the **MEAN** of each bucket
   (`Series.resample(freq).mean()`). A bucket with no usable reading is `NaN`.
6. Linearly **interpolate interior gaps only**:
   `interpolate(method="linear", limit_area="inside")` so that leading and
   trailing `NaN` buckets are **NOT** filled.
7. Compute outlier flags from the cleaned (post-interpolation) values using
   `scipy.stats.zscore` with `nan_policy="omit"`; a bucket is an outlier when
   `abs(z) > 3.0`. Buckets whose z is `NaN` (still-empty buckets, or a
   constant input where the z is undefined) are **not** outliers.
8. Compute `mean` and `std` over the **non-NaN** cleaned values only, using
   `numpy.nanmean` and `numpy.nanstd` (the std uses `ddof=1`, the sample std).

### Return value

Return a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `index` | list[str] | ISO-8601 timestamp of each bucket on the regular grid, in ascending order. |
| `values` | list[float or None] | The cleaned value of each bucket; `None` for a bucket that is still `NaN` after interior-only interpolation. Same length as `index`. |
| `outliers` | list[bool] | `True` where `abs(z) > 3.0`, else `False`. Same length as `index`. |
| `n_interpolated` | int | Number of buckets that were `NaN` after resampling **and** became non-`NaN` after interior interpolation. |
| `mean` | float | `numpy.nanmean` over the non-NaN cleaned values. |
| `std` | float | `numpy.nanstd(..., ddof=1)` over the non-NaN cleaned values. |

### Exception contract

`resample_clean` **raises `ValueError`** when:

* `readings` is empty.
* any `ts` cannot be parsed as a timestamp.
* `freq` is not a valid pandas offset alias.

An input where **all values are equal** must **not** crash: the z-scores are
undefined (constant series), which is treated as **no outliers**, and `mean` /
`std` are still returned (`std` will be `0.0`).

## Notes

* `scipy.stats.zscore` must appear in your source (surface-form check).
* Compare floats with a tolerance, never `==`.
* Determinism: the grader builds a fixed readings list inline; do not generate
  random data.
* There is **no** CLI for this task.
