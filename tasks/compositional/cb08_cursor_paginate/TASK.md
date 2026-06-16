# Compositional 08 — `cursor_paginate`: Stable Cursor Pagination over a Sorted DataFrame

**Created:** 2026-06-16 · **Category:** compositional · **Weight:** 4

Implement stable, cursor-based ("keyset") pagination over a sorted pandas
DataFrame. The difficulty is entirely in the **ordering semantics**: the cursor
is **exclusive**, ties on the sort column are broken by a stable `id`, and there
is **never a trailing empty page**. Misreading any one of these duplicates or
drops a row during a full walk.

Implement your solution in a single file `solution.py`. It composes **pandas**
(the table + ordering), **json** (the cursor payload), and **base64** (the opaque
token).

## Public contract

### `paginate(df: pandas.DataFrame, sort_key: str, page_size: int, cursor: str | None = None) -> dict`

Return one page of `df` under stable cursor pagination.

**Ordering (total order).** Rows are ordered by `(df[sort_key] ASC, df["id"] ASC)`.
Assume an integer column named `"id"` whose values are **unique**; it is the
**stable tie-breaker** so two rows with the same `sort_key` value can never swap
places between calls. `sort_key` may be any orderable column (e.g. an `int` or
`str` "score"/"name" column).

**The cursor is EXCLUSIVE.** A page returns the first `page_size` rows that come
**strictly after** the cursor position in the order above. "Strictly after" means
the row's `(sort_key, id)` pair is **lexicographically greater** than the
cursor's `(sort_key, id)` pair. The row that produced the cursor is therefore
**never repeated**. Because ties on `sort_key` are broken by `id` ascending,
pagination never skips and never duplicates a tied row, even when a block of
equal `sort_key` values straddles a page boundary.

* `cursor = None` (the default) starts at the very **beginning** of the order.

**The cursor token** is an **opaque** `base64` encoding of a `json` array holding
the last returned row's `[sort_key value, id]`. Treat it as opaque: it is
produced only by this function and only ever consumed by this function. (Any
self-consistent `base64(json([sort_value, id]))` encoding is acceptable — the
grader only round-trips tokens your function returns, never hand-built ones.)

**Return value.** A dict with **exactly** these keys:

| Key | Type | Description |
|-----|------|-------------|
| `rows` | `list[dict]` | The page rows as record dicts (`DataFrame.to_dict(orient="records")` shape), in `(sort_key, id)` order. |
| `next_cursor` | `str \| None` | The opaque token for the **last returned row**, or `None` when that row is the **last row of the whole ordering**. |

**No trailing empty page.** `next_cursor` is `None` exactly when the page ends on
the final row of the order. In particular, if exactly `page_size` rows remain and
they are the final rows, `next_cursor` is `None` (a subsequent call would return
zero rows — that empty page must never be reachable through the cursor chain). If
the page is full **and** more rows remain, `next_cursor` is the token of the
page's last row.

### Exception contract

| Condition | Raise |
|-----------|-------|
| `cursor` is a malformed / undecodable token (not valid `base64(json([value, id]))`) | `ValueError` |
| `page_size < 1` | `ValueError` |
| the `"id"` column is missing from `df` | `KeyError` |
| the `sort_key` column is missing from `df` | `KeyError` |

Assert exception **types**; messages are unspecified.

## Worked example

`df` has rows (already shown in `(sort_key, id)` order) where `sort_key="score"`:

```
score=10 id=1
score=10 id=2     <- tied block on score=10 spans the page boundary
score=10 id=5
score=20 id=3
score=20 id=4
```

With `page_size=2`:

* Call 1 (`cursor=None`) → rows `[(10,1), (10,2)]`, `next_cursor` = token of `(10, 2)`.
* Call 2 (`cursor=token(10,2)`) → rows `[(10,5), (20,3)]` (the tied `(10,5)` is
  **not** skipped and `(10,2)` is **not** repeated), `next_cursor` = token of `(20, 3)`.
* Call 3 (`cursor=token(20,3)`) → rows `[(20,4)]`, `next_cursor` = `None`
  (last row reached; no trailing empty page).

Walking the cursor chain from `None` until `next_cursor is None` must yield
**every row exactly once, in order, with no duplicates and no omissions.**

## Notes

* `pandas` must appear in your source and be used for the ordering (surface-form check).
* `base64` must appear in your source (the token is base64-encoded).
* The function is **pure**: it must not mutate `df`.
* Determinism: the order is fully determined by `(sort_key, id)`; no seeds needed.
