"""http.py — Request and Response classes for the WSGI micro-framework."""

import json
import urllib.parse
import http as _http_module


class Request:
    """Wraps a WSGI environ dict."""

    def __init__(self, environ: dict) -> None:
        self.environ = environ
        self.method: str = environ.get("REQUEST_METHOD", "GET").upper()
        self.path: str = environ.get("PATH_INFO", "/")
        self.query_string: str = environ.get("QUERY_STRING", "")
        # Read body safely, guarding against missing or empty CONTENT_LENGTH
        content_length_raw = environ.get("CONTENT_LENGTH", "")
        length = int(content_length_raw) if content_length_raw else 0
        self.body: bytes = environ["wsgi.input"].read(length) if length > 0 else b""
        self.path_params: dict = {}

    def get_json(self) -> object:
        """Parse body as JSON and return the decoded object.
        Raise ValueError if the body is empty or not valid JSON."""
        if not self.body:
            raise ValueError("Empty body; cannot parse JSON.")
        return json.loads(self.body)

    def query_params(self) -> dict:
        """Return a dict of query-string key→value pairs (first value wins for
        duplicates). Returns {} for an empty query string."""
        if not self.query_string:
            return {}
        parsed = urllib.parse.parse_qs(self.query_string, keep_blank_values=False)
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
        # Build status string using stdlib http.HTTPStatus for phrase lookup
        _STATUS_PHRASES = {
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
        }
        phrase = _STATUS_PHRASES.get(self.status_code)
        if phrase is None:
            try:
                phrase = _http_module.HTTPStatus(self.status_code).phrase
            except ValueError:
                phrase = "Unknown"
        status_str = f"{self.status_code} {phrase}"
        header_list = list(self.headers.items())
        start_response(status_str, header_list)
        return [self.body]
