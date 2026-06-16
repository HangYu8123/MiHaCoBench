# Compositional 01 — `log_analytics`: HTTP Access-Log Analytics

**Created:** 2026-06-15 · **Category:** compositional · **Weight:** 4

Analyse a pre-collected HTTP access-log dataset stored at `data/access_log.csv`
(committed in the task directory). The CSV has three columns:

| Column | Type | Description |
|--------|------|-------------|
| `endpoint` | str | URL path string, e.g. `"/api/users"` |
| `latency_ms` | float | Request latency in milliseconds |
| `status` | int | HTTP response status code |

Implement your solution in a single file `solution.py`.

## Public contract

### `analyze_logs(df: pandas.DataFrame) -> dict`

Analyse the log DataFrame and return a summary dict.

**Raises `ValueError`** if `df` is empty.

Return a dict with **exactly** these top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `per_endpoint` | dict | Per-endpoint statistics (see below) |
| `slowest_endpoint` | str | Endpoint with the highest `p95_latency` |
| `anomalies` | list[str] | Endpoints whose p95 z-score across all endpoints is > 2.0 |

#### `per_endpoint` structure

`per_endpoint` maps each endpoint string to a sub-dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `count` | int | Total number of requests |
| `p95_latency` | float | 95th-percentile latency in ms (use `numpy.percentile` with `q=95`) |
| `error_rate` | float | Fraction of requests with `status >= 500` |

Use `pandas.DataFrame.groupby("endpoint")` to group rows.

#### `slowest_endpoint`

The endpoint name (str) with the highest `p95_latency`. If there is a tie, any
tied endpoint is acceptable.

#### `anomalies`

A list of endpoint strings whose **p95_latency** z-score (computed with
`scipy.stats.zscore` across all endpoints' p95 values) is strictly greater than
2.0. The list may be empty. Order does not matter.

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze_logs`, and writes inside
`<dir>`:

1. **`results.json`** — `json.dumps(analyze_logs(df))` (all keys present).
2. **`latency.png`** — a bar chart of `p95_latency` per endpoint.

Both files must be written; `latency.png` must be a valid PNG. Do not call
`plt.show()` — set `matplotlib.use("Agg")` or rely on `MPLBACKEND=Agg`.

Exit code `0` on success, non-zero on error.

## Notes

* `pandas.DataFrame.groupby` must appear in your source (surface-form check).
* `numpy.percentile` or `pandas` quantile must appear in your source.
* Seeds/determinism are not required; the dataset is fixed.
* Do not modify the CSV file.
