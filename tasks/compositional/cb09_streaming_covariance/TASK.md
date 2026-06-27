# Compositional 09 — `streaming_covariance`: single-pass numerically-stable statistics

**Created:** 2026-06-17 · **Category:** compositional · **Weight:** 4

Compute mean, variance, covariance, and Pearson correlation over a stream of
`(x, y)` pairs **in a single pass using bounded memory**. The stream may be a
generator yielding millions of pairs, so you must **not** materialise it into a
list and must **not** iterate it more than once.

The difficulty is **numerical**: the data can carry a large constant offset
(values around `1e9` with a true variance around `100`). The familiar
"sum of squares minus square of the sum" identity is algebraically correct but
loses all precision here — you need a numerically stable single-pass method.

Implement your solution in a single file `solution.py`. It composes **numpy**
(assemble/return the result vector) with a pure-Python streaming accumulator.

## Public contract

### `streaming_stats(pairs: collections.abc.Iterable[tuple[float, float]]) -> dict`

Consume `pairs` exactly once and return a dict with **exactly** these keys:

| Key | Type | Meaning |
|-----|------|---------|
| `n` | `int` | number of pairs consumed |
| `mean_x` | `float` | mean of the x values |
| `mean_y` | `float` | mean of the y values |
| `var_x` | `float` | **population** variance of x (ddof = 0) |
| `var_y` | `float` | **population** variance of y (ddof = 0) |
| `cov` | `float` | **population** covariance of x and y (ddof = 0) |
| `corr` | `float` | Pearson correlation `cov / sqrt(var_x * var_y)` |

**Accuracy.** Results must be correct to a relative tolerance of `1e-6` even when
the inputs have a large constant offset. (This is what rules out the naive
sum-of-squares formula.)

**Memory / passes.** Use **O(1)** additional memory: a fixed set of running
accumulators, independent of `n`. Iterate `pairs` **once**.

### Exception / boundary contract

| Condition | Behaviour |
|-----------|-----------|
| `pairs` is empty (`n == 0`) | raise `ValueError` |
| `var_x == 0` or `var_y == 0` (correlation undefined) | set `"corr"` to `0.0` (do **not** divide by zero) |

Assert exception **types**; messages are unspecified.

## Notes

* `numpy` must appear in your source and be used (surface-form check).
* Determinism: the result is a pure function of the consumed values.
* Population (ddof = 0) statistics throughout — matches `numpy.var(..., ddof=0)`
  and `numpy.cov(..., bias=True)`.
