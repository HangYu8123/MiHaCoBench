# Data Analysis 03 — `customer_segments`: KMeans Customer Segmentation

**Created:** 2026-06-15 · **Category:** data_analysis · **Weight:** 3

Segment a synthetic customer dataset stored at `data/customers.csv`
(committed in the task directory). The CSV has three numeric columns:

| Column | Type | Description |
|--------|------|-------------|
| `recency` | float | Days since last purchase (scaled) |
| `frequency` | float | Purchase frequency (scaled) |
| `monetary` | float | Spend value (scaled) |

Implement your solution in a single file `solution.py`.

## Public contract

### `analyze(df: pandas.DataFrame) -> dict`

Perform KMeans customer segmentation. You **must**:

1. Standardize the three features using `sklearn.preprocessing.StandardScaler`
   (fit and transform on the full DataFrame).
2. Run `sklearn.cluster.KMeans` with `random_state=0` and `n_init=10` for each
   `k` in `{2, 3, 4, 5, 6}`.
3. Compute `sklearn.metrics.silhouette_score` for each `k` on the scaled data.
4. Choose `best_k` as the `k` with the **highest** silhouette score.
5. Refit KMeans with `best_k` (same `random_state=0`, `n_init=10`) to obtain
   final cluster labels.

Return a dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `best_k` | `int` | k with the highest silhouette score |
| `silhouette` | `float` | Silhouette score for `best_k` |
| `inertia_by_k` | `{str(k): float}` | KMeans inertia for each k tried (`"2"` through `"6"`) |
| `cluster_sizes` | `list[int]` | Cluster membership counts for `best_k`, sorted **descending** |

### `main(argv: list[str] | None = None) -> int`

CLI entry point:

```
python solution.py --data <csv_path> --output-dir <dir>
```

Reads the CSV with `pandas.read_csv`, calls `analyze`, and writes to `<dir>`:

1. **`results.json`** — `json.dumps(analyze(df))` (all keys present).
2. **Three or more PNG files** (any filenames, ending in `.png`):
   - Elbow curve: inertia vs k (for k in 2..6).
   - Silhouette score vs k (for k in 2..6).
   - 2D PCA scatter plot of the scaled data colored by cluster assignment
     (use `sklearn.decomposition.PCA` to reduce to 2 components).

All figures must be saved as PNGs (no interactive display).

Exit code `0` on success, non-zero on error.

## Notes

* `KMeans`, `silhouette_score`, and `StandardScaler` must appear in your source
  (surface-form check).
* `random_state=0` and `n_init=10` are required for determinism.
* Do not modify the CSV file.
