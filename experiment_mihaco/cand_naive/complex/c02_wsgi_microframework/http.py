"""http.py — Request and Response classes for the WSGI micro-framework."""

import json
import urllib.parse


class Request:
    """Wraps a WSGI environ dict."""

    def __init__(self, environ: dict) -> None:
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO", "/")
        self.query_string = environ.get("QUERY_STRING", "")
        self.path_params: dict = {}

        # Read body up to CONTENT_LENGTH
        content_length = environ.get("CONTENT_LENGTH", "")
        try:
            length = int(content_length) if content_length else 0
        except (ValueError, TypeError):
            length = 0

        wsgi_input = environ.get("wsgi.input")
        if wsgi_input is not None and length > 0:
            self.body = wsgi_input.read(length)
        else:
            self.body = b""

    def get_json(self) -> object:
        """Parse body as JSON and return the decoded object.

        Raises ValueError if the body is empty or not valid JSON.
        """
        if not self.body:
            raise ValueError("Empty body — cannot parse as JSON")
        return json.loads(self.body.decode("utf-8"))

    def query_params(self) -> dict:
        """Return a dict of query-string key→value pairs (first value wins for
        duplicates). Returns {} for an empty query string."""
        if not self.query_string:
            return {}
        parsed = urllib.parse.parse_qs(self.query_string, keep_blank_values=True)
        # parse_qs returns lists; take the first value for each key
        return {k: v[0] for k, v in parsed.items()}


# HTTP status reason phrases
_STATUS_PHRASES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


class Response:
    """Mutable HTTP response."""

    def __init__(self) -> None:
        self.status_code: int = 200
        self.headers: dict = {"Content-Type": "text/html; charset=utf-8"}
        self.body: bytes = b""

    def set_json(self, data: object) -> None:
        """Serialise *data* to JSON, set body, and set Content-Type to application/json."""
        self.body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        self.headers["Content-Type"] = "application/json"

    def __call__(self, environ: dict, start_response) -> list:
        """Make Response a valid WSGI response: call start_response, return [body]."""
        reason = _STATUS_PHRASES.get(self.status_code, "Unknown")
        status = f"{self.status_code} {reason}"
        # Build header list
        header_list = list(self.headers.items())
        start_response(status, header_list)
        return [self.body]
