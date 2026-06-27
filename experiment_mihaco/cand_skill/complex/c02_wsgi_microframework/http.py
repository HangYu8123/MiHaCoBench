"""WSGI micro-framework — http.py: Request and Response classes."""

import json
import urllib.parse

# Status-text lookup for common HTTP status codes.
# We avoid importing from the stdlib 'http' module here because this file
# is *also* named http.py and would shadow it when on sys.path.
_STATUS_TEXT: dict = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


class Request:
    """Wraps a WSGI environ dict."""

    def __init__(self, environ: dict) -> None:
        self.environ = environ
        self.method: str = environ.get("REQUEST_METHOD", "GET")
        self.path: str = environ.get("PATH_INFO", "/")
        self.query_string: str = environ.get("QUERY_STRING", "")
        length = int(environ.get("CONTENT_LENGTH") or 0)
        self.body: bytes = environ["wsgi.input"].read(length) if length > 0 else b""
        self.path_params: dict = {}

    def get_json(self) -> object:
        """Parse body as JSON and return the decoded object.
        Raise ValueError if the body is empty or not valid JSON."""
        if not self.body:
            raise ValueError("Empty body — cannot decode JSON")
        try:
            return json.loads(self.body)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc

    def query_params(self) -> dict:
        """Return a dict of query-string key→value pairs (first value wins for
        duplicates). Returns {} for an empty query string."""
        if not self.query_string:
            return {}
        parsed = urllib.parse.parse_qs(self.query_string, keep_blank_values=True)
        return {k: v[0] for k, v in parsed.items()}


class Response:
    """Mutable HTTP response."""

    def __init__(self) -> None:
        self.status_code: int = 200
        self.headers: dict = {"Content-Type": "text/html; charset=utf-8"}
        self.body: bytes = b""

    def set_json(self, data: object) -> None:
        """Serialise *data* to JSON, set body, and set Content-Type to application/json."""
        self.body = json.dumps(data).encode("utf-8")
        self.headers["Content-Type"] = "application/json"

    def __call__(self, environ: dict, start_response) -> list:
        """Make Response a valid WSGI response: call start_response, return [body]."""
        phrase = _STATUS_TEXT.get(self.status_code, "Unknown")
        status = f"{self.status_code} {phrase}"
        header_list = list(self.headers.items())
        start_response(status, header_list)
        return [self.body]
