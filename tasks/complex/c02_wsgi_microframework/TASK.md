# Complex 02 — `c02_wsgi_microframework`: WSGI Micro-Framework

**Created:** 2026-06-15 · **Category:** complex · **Weight:** 5

Build a small WSGI micro-framework spread across several modules, then wire it
into a demo application via a factory function.  A live server is **never
started**; the grader calls the WSGI app directly with synthetic `environ`
dicts.

## File layout (you must create all of these)

```
http.py           # Request and Response classes
router.py         # Route + Router (path converters)
middleware.py     # middleware chain
app.py            # App class
app_factory.py    # create_app() — the graded entry point
```

All files live in the **same directory** as one another (flat layout, no
sub-packages).

---

## Module contracts

### `http.py`

```python
class Request:
    """Wraps a WSGI environ dict."""
    environ: dict                  # the raw environ
    method: str                    # e.g. "GET"
    path: str                      # e.g. "/hello/world"
    query_string: str              # raw query string, e.g. "a=1&b=2"
    body: bytes                    # read from wsgi.input up to CONTENT_LENGTH
    path_params: dict              # populated by the router after matching

    def get_json(self) -> object:
        """Parse body as JSON and return the decoded object. Raise ValueError if
        the body is empty or not valid JSON."""

    def query_params(self) -> dict[str, str]:
        """Return a dict of query-string key→value pairs (first value wins for
        duplicates). Returns {} for an empty query string."""


class Response:
    """Mutable HTTP response."""
    status_code: int               # default 200
    headers: dict[str, str]        # starts with {"Content-Type": "text/html; charset=utf-8"}
    body: bytes                    # default b""

    def set_json(self, data: object) -> None:
        """Serialise *data* to JSON, set body, and set
        Content-Type to application/json."""

    def __call__(self, environ: dict, start_response) -> list[bytes]:
        """Make Response a valid WSGI response: call start_response, return [body]."""
```

### `router.py`

```python
class Route:
    """Represents a single URL rule."""
    path_template: str             # e.g. "/hello/<name>" or "/add"
    methods: list[str]             # upper-cased HTTP methods
    handler: callable              # view function

class Router:
    """Match incoming paths to registered routes."""

    def add_route(self, path_template: str, methods: list[str], handler) -> None:
        """Register a new Route."""

    def match(self, path: str, method: str) -> tuple[callable, dict] | tuple[None, int]:
        """Match *path* and *method*.

        Returns ``(handler, path_params)`` on success.
        Returns ``(None, 404)`` if no route matches the path.
        Returns ``(None, 405)`` if the path matches but the method does not.

        Path converters supported:
          * ``<name>``       — matches any non-empty path segment, captured as str.
          * ``<int:name>``   — matches a decimal-integer segment, captured as int.
        """
```

### `middleware.py`

```python
class MiddlewareChain:
    """Wraps a WSGI app with an ordered list of middleware callables.

    Each middleware has the signature:
        middleware(environ, start_response, next_app) -> list[bytes]
    """

    def __init__(self, app) -> None: ...

    def use(self, middleware_fn) -> None:
        """Append *middleware_fn* to the chain."""

    def __call__(self, environ, start_response) -> list[bytes]:
        """Invoke the chain, falling through to the inner app."""
```

### `app.py`

```python
class App:
    """Core WSGI application."""

    def __init__(self) -> None: ...

    def route(self, path: str, methods: list[str] | None = None):
        """Decorator factory: register the decorated function as the handler for
        *path* + *methods* (default ``["GET"]``)."""

    def __call__(self, environ: dict, start_response) -> list[bytes]:
        """WSGI entry point.  Dispatch the request; return the response body."""
```

### `app_factory.py`

```python
def create_app() -> callable:
    """Build and return a WSGI-compatible callable (the demo application).

    The returned callable must implement every route listed below.
    """
```

---

## Demo-application routes (implemented inside `create_app`)

| Method | Path | Success response |
|--------|------|-----------------|
| `GET` | `/` | 200, `Content-Type: text/html`, body contains the text `"PyBench"` (rendered via **jinja2**) |
| `GET` | `/hello/<name>` | 200, `Content-Type: application/json`, body `{"greeting": "Hello, <name>!"}` |
| `GET` | `/add` | query params `a` and `b`: 200 JSON `{"sum": <int>}` when both parse as `int`; 400 JSON `{"error": "..."}` when they do not |
| `POST` | `/echo` | reads JSON body, 200 JSON `{"you_sent": <parsed body>}` |
| _any unknown path_ | | 404 JSON `{"error": "not found"}` |
| _wrong method on a known path_ | | 405 JSON `{"error": "method not allowed"}` |

The `/add` route **must** use the router's `<int:name>` converter (typed
integer path-param parsing); but since `/add` takes its numbers from the
**query string** rather than the path, the convention here is:

* Register `/add` as a plain path (no converters in the URL template itself).
* In the handler, call `request.query_params()`, attempt `int()` conversion of
  `a` and `b`; if either fails, return a 400 response.

---

## Output contract summary

* All JSON responses use `Content-Type: application/json`.
* The HTML response at `/` uses `Content-Type: text/html` (any charset suffix
  is accepted).
* Status codes are conveyed in the WSGI `status` string passed to
  `start_response`, e.g. `"200 OK"`, `"404 Not Found"`.
* The grader calls the WSGI app directly — no `werkzeug`, no live socket.

## Notes

* Use only packages in `requirements.txt` plus the Python standard library
  (`wsgiref`, `json`, `io`, `http`, `urllib.parse`).
* Determinism: fixed seeds are not required (no randomness).
