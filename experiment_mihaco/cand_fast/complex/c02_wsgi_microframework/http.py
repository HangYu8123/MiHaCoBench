"""http.py — Request and Response classes for the WSGI micro-framework."""

import json
import urllib.parse

# HTTP status code -> reason phrase
_STATUS_PHRASES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}


class Request:
    """Wraps a WSGI environ dict."""

    def __init__(self, environ: dict) -> None:
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO", "/")
        self.query_string = environ.get("QUERY_STRING", "")
        # Read body from wsgi.input up to CONTENT_LENGTH bytes at init time.
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
        if content_length > 0:
            self.body = environ["wsgi.input"].read(content_length)
        else:
            self.body = b""
        # Populated by the router after matching
        self.path_params: dict = {}

    def get_json(self) -> object:
        """Parse body as JSON and return the decoded object.
        Raises ValueError if the body is empty or not valid JSON."""
        if not self.body:
            raise ValueError("Empty body cannot be parsed as JSON")
        return json.loads(self.body)

    def query_params(self) -> dict:
        """Return a dict of query-string key->value pairs (first value wins
        for duplicates). Returns {} for an empty query string."""
        if not self.query_string:
            return {}
        parsed = urllib.parse.parse_qs(self.query_string, keep_blank_values=True)
        # parse_qs returns list values; take the first value for each key
        return {k: v[0] for k, v in parsed.items()}


class Response:
    """Mutable HTTP response."""

    def __init__(self, status_code: int = 200, body: bytes = b"") -> None:
        self.status_code = status_code
        self.headers: dict = {"Content-Type": "text/html; charset=utf-8"}
        self.body = body

    def set_json(self, data: object) -> None:
        """Serialise data to JSON, set body, and set Content-Type to
        application/json."""
        self.body = json.dumps(data).encode("utf-8")
        self.headers["Content-Type"] = "application/json"

    def __call__(self, environ: dict, start_response) -> list:
        """Make Response a valid WSGI response: call start_response, return [body]."""
        reason = _STATUS_PHRASES.get(self.status_code, "Unknown")
        status_str = f"{self.status_code} {reason}"
        headers_list = list(self.headers.items())
        start_response(status_str, headers_list)
        return [self.body]
