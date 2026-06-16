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
    # BUG: only the LEADING slash is stripped and empty segments are NOT
    # dropped, so a trailing slash leaves a stray "" segment:
    #   "/users/5/" -> ["users", "5", ""]   (length 3, no longer matches a
    #   length-2 pattern).  Paths without a trailing slash are unaffected.
    return p.lstrip("/").split("/")
