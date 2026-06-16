# Debug 04 — `paginate`: every page skips its first row

**Created:** 2026-06-15 · **Category:** debug · **Weight:** 2

You are given a **buggy** pagination helper. Find and fix the defect, then write
your corrected solution as `solution.py` (**standard library only**). Keep the
public contract below exactly; do not rename the function.

## Buggy implementation

```python
def paginate(records, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    start = page * page_size
    return list(records[start:start + page_size])
```

## Symptom (failing behavior)

Pages are **1-indexed**, so page 1 should return the first `page_size` records.
Instead the helper returns the *second* page's records for page 1, and the very
first record is never returned:

```text
>>> paginate([10, 20, 30, 40, 50], page=1, page_size=2)
[30, 40]    # actual   (wrong)
[10, 20]    # expected
```

Argument validation and out-of-range pages (which correctly return `[]`) are
already fine — only the slice boundary is wrong.

## Public contract (must match exactly)

```python
def paginate(records: Sequence, page: int, page_size: int) -> list:
    ...
```

* Pages are 1-indexed: page 1 → `records[0:page_size]`, page 2 →
  `records[page_size:2*page_size]`, etc.
* The final page may be short; a page past the end returns `[]`.
* `page < 1` or `page_size < 1` raises `ValueError`.
* Return a `list` (the slice of `records`).

## Notes

* Standard library only. Assert exceptions by **type** (`ValueError`).
* Determinism: identical input ⇒ identical output.
