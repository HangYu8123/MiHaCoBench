"""path.py — URL path normalization helper for the tiny router.

Holds the single function used by BOTH the router (when registering patterns)
and the app (when handling incoming paths), so that pattern/path comparison is
always done on the same normalized segment lists.
"""
from __future__ import annotations


def split_path(p: str) -> list[str]:
    """Normalize a URL path into its non-empty segments.

    Leading and trailing slashes are stripped and empty segments (produced by
    duplicate or boundary slashes) are dropped. Therefore::

        "/users/5"   -> ["users", "5"]
        "/users/5/"  -> ["users", "5"]
        "users/5"    -> ["users", "5"]
        "/"          -> []
        ""           -> []
    """
    return [seg for seg in p.strip("/").split("/") if seg]
