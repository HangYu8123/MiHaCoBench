"""Gold reference for debug/dbg04_paginate — 1-indexed pagination (stdlib only).

The original code converted a 1-indexed page number to a 0-indexed slice offset
without subtracting one, so every page skipped its first record and bled one
record in from the next page. The fix uses ``start = (page - 1) * page_size``.
"""
from __future__ import annotations

from typing import Sequence


def paginate(records: Sequence, page: int, page_size: int) -> list:
    """Return the slice of ``records`` for the 1-indexed ``page``.

    Page 1 is ``records[0:page_size]``, page 2 is ``records[page_size:2*page_size]``,
    and so on. The final page may be short; a page past the end yields ``[]``.
    ``page < 1`` or ``page_size < 1`` raises ``ValueError``.
    """
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    start = (page - 1) * page_size
    return list(records[start:start + page_size])
