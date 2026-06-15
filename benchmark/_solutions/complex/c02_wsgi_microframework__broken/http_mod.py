"""Gold reference — http_mod.py: Request and Response wrappers.

Named http_mod (not http) to avoid shadowing the stdlib http package.
"""
from __future__ import annotations

import json
import urllib.parse
from typing import Any


class Request:
    """Wraps a WSGI environ dict and exposes a convenient API."""

    def __init__(self, environ: dict) -> None:
        self.environ = environ
        self.method: str = environ.get("REQUEST_METHOD", "GET").upper()
        self.path: str = environ.get("PATH_INFO", "/")
        self.query_string: str = environ.get("QUERY_STRING", "")
        # read body
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except (ValueError, TypeError):
            length = 0
        wsgi_input = environ.get("wsgi.input")
        self.body: bytes = wsgi_input.read(length) if wsgi_input and length > 0 else b""
        # path_params populated by router after matching
        self.path_params: dict = {}

    def get_json(self) -> Any:
        """Parse body as JSON; raise ValueError if empty or invalid."""
        if not self.body:
            raise ValueError("empty request body")
        return json.loads(self.body.decode("utf-8"))

    def query_params(self) -> dict[str, str]:
        """Return query-string params as {key: first_value}."""
        if not self.query_string:
            return {}
        parsed = urllib.parse.parse_qs(self.query_string, keep_blank_values=True)
        return {k: v[0] for k, v in parsed.items()}


class Response:
    """Mutable HTTP response that is also a WSGI callable."""

    def __init__(self, status_code: int = 200, body: bytes = b"") -> None:
        self.status_code: int = status_code
        self.headers: dict[str, str] = {"Content-Type": "text/html; charset=utf-8"}
        self.body: bytes = body

    _STATUS_PHRASES: dict[int, str] = {
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
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }

    def _status_str(self) -> str:
        phrase = self._STATUS_PHRASES.get(self.status_code, "Unknown")
        return f"{self.status_code} {phrase}"

    def set_json(self, data: Any) -> None:
        """Serialise *data* to JSON and set Content-Type to application/json."""
        self.body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        self.headers["Content-Type"] = "application/json"

    def __call__(self, environ: dict, start_response) -> list[bytes]:
        """WSGI response callable."""
        header_list = list(self.headers.items())
        start_response(self._status_str(), header_list)
        return [self.body]
