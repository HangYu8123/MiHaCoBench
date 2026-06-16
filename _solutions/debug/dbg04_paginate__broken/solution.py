"""Deliberately-broken reference for debug/dbg04_paginate.

Planted defect (a classic 1-indexed off-by-one): the page number is multiplied
by ``page_size`` without the ``- 1`` needed to map a 1-indexed page onto a
0-indexed offset, so page 1 returns the *second* page's records and the very
first record is never returned. Argument validation and out-of-range handling are
correct, so the defect is localized to the slice boundary.
"""
from __future__ import annotations

from typing import Sequence


def paginate(records: Sequence, page: int, page_size: int) -> list:
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    start = page * page_size  # 1-indexed page used as a 0-indexed offset
    return list(records[start:start + page_size])
