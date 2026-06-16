"""http.py — Request and Response classes for the WSGI micro-framework."""

import json
import urllib.parse


class Request:
    """Wraps a WSGI environ dict."""

    def __init__(self, environ: dict) -> None:
        self.environ = environ
        self.method: str = environ["REQUEST_METHOD"]
        self.path: str = environ["PATH_INFO"]
        self.query_string: str = environ.get("QUERY_STRING", "")
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
        if content_length > 0:
            self.body: bytes = environ["wsgi.input"].read(content_length)
        else:
            self.body: bytes = b""
        self.path_params: dict = {}

    def get_json(self) -> object:
        """Parse body as JSON and return the decoded object.

        Raises ValueError if the body is empty or not valid JSON.
        """
        if not self.body:
            raise ValueError("Empty body")
        return json.loads(self.body)

    def query_params(self) -> dict:
        """Return a dict of query-string key→value pairs (first value wins for
        duplicates). Returns {} for an empty query string.
        """
        result = urllib.parse.parse_qs(self.query_string, keep_blank_values=False)
        return {k: v[0] for k, v in result.items()}


class Response:
    """Mutable HTTP response."""

    _STATUS_MAP = {
        200: "200 OK",
        400: "400 Bad Request",
        404: "404 Not Found",
        405: "405 Method Not Allowed",
    }

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
        status = self._STATUS_MAP.get(self.status_code, f"{self.status_code} Unknown")
        header_list = list(self.headers.items())
        start_response(status, header_list)
        return [self.body]
