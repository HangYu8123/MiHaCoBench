"""Deliberately-broken reference for debug/dbg05_group_tally.

Planted defect (the classic mutable-default-argument footgun): ``groups={}`` is
evaluated once when the function is defined, so every call that omits ``groups``
shares and mutates the same dict — state from one call leaks into the next. When
a caller passes an explicit ``groups`` dict the default is bypassed and behaviour
is correct, so the defect is localized to the no-argument path.
"""
from __future__ import annotations

from typing import Any


def tally_by_group(label: str, value: Any, groups: dict = {}) -> dict:
    groups.setdefault(label, []).append(value)
    return groups
