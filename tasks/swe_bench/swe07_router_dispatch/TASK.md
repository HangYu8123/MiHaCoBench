# SWE-Bench 07 — `router_dispatch`: Tiny Path Router with Typed Params

**Created:** 2026-06-16 · **Category:** swe_bench · **Weight:** 6

Implement (and debug) a tiny URL path router with named path
parameters, structured as three modules. A trailing-slash bug crosses a
module boundary: the **symptom** is observed through `app.App.handle`
(in `app.py`), but the **root cause** lives in `path.py`.

```
path.py     — split_path(p): normalize a URL path into its segments  (HOLDS THE BUG)
router.py   — class Router: pattern registration + matching
app.py      — FACADE: class App (route + handle)
```

---

## Files to create

```
path.py     — function split_path(p: str) -> list[str]
router.py   — class Router
app.py      — FACADE: class App  (must allow `from app import App`)
```

Use **stdlib only** — no third-party packages.

---

## Public contract

### `path.py`

```python
def split_path(p: str) -> list[str]:
    """Normalize a URL path into its NON-EMPTY segments."""
```

Strip leading **and** trailing slashes and drop any empty segments, so:

| Input | Output |
|---|---|
| `"/users/5"`  | `["users", "5"]` |
| `"/users/5/"` | `["users", "5"]` |
| `"users/5"`   | `["users", "5"]` |
| `"/"`         | `[]` |
| `""`          | `[]` |

### `router.py`

```python
class Router:
    def add(self, pattern: str, handler_name: str) -> None:
        """Register handler_name for pattern (e.g. "/users/{id}/posts/{pid}")."""

    def match(self, path: str) -> tuple[str, dict] | None:
        """Return (handler_name, params) for the first matching route, else None."""
```

Matching rules — use `path.split_path` for **both** the pattern and the
incoming path:

- A route matches **iff** `split_path(pattern)` and `split_path(path)`
  have **EQUAL length**, AND every literal pattern segment equals the
  corresponding path segment.
- A `{name}` pattern segment is a **capture**: it matches any single path
  segment and binds that segment **as a string** into `params` under key
  `name` (e.g. `{id}` captures into `params["id"]`).
- Routes are tried in registration order; the first match wins.
- On no match, `match` returns `None`.

### `app.py` (facade)

```python
class App:
    def __init__(self) -> None: ...

    def route(self, pattern: str, handler_name: str) -> None:
        """Register a route (delegates to Router.add)."""

    def handle(self, path: str) -> dict:
        """Dispatch path. Returns:
             {"handler": <name>, "params": {...}}  on a match
             {"handler": None, "params": {}}       on no match
        """
```

`app.py` must allow `from app import App`.

Exact `handle` output contract (dict, these keys exactly):
- match: `{"handler": <handler_name str>, "params": <dict of str->str>}`
- no match: `{"handler": None, "params": {}}`

Captured parameter **values are strings** (e.g. `"5"`, not `5`).

---

## Known bug description (for SWE-bench fault localisation)

**Symptom (via `app.App.handle`):** a path that is identical to a working
one except for a **trailing slash** fails to route. For example, with a
route `"/users/{id}"` registered:

```python
app.handle("/users/5")    # -> {"handler": "show", "params": {"id": "5"}}   (works)
app.handle("/users/5/")   # -> {"handler": None,   "params": {}}            (BUG)
```

**Root cause (in `path.py`):** `split_path` strips only the **leading**
slash and does not drop empty segments, so `"/users/5/"` normalizes to
`["users", "5", ""]` (length 3) instead of `["users", "5"]` (length 2),
and no longer matches the length-2 pattern. Paths **without** a trailing
slash are unaffected, which is why static routes, single-param routes,
and two-param routes all work until a trailing slash appears.

**Your task:** fix `split_path` so leading **and** trailing slashes are
stripped and empty segments dropped, so `"/users/5"`, `"/users/5/"`, and
`"users/5"` all normalize to `["users", "5"]`, while `"/"` and `""`
normalize to `[]`.

---

## Constraints

- **stdlib only** — no third-party packages.
- The router must use `path.split_path` for BOTH the pattern and the path
  (do not normalize them differently).
- Captured `{name}` values are returned as strings.
- The grader imports `App` from `app.py` only.
