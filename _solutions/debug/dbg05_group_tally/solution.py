"""Gold reference for debug/dbg05_group_tally — grouped accumulation (stdlib only).

The original used a mutable dict as the default argument, so every call that
omitted ``groups`` shared one dict created at definition time — state leaked
across independent calls. The fix uses a ``None`` sentinel and creates a fresh
dict per call.
"""
from __future__ import annotations

from typing import Any


def tally_by_group(label: str, value: Any, groups: dict | None = None) -> dict:
    """Append ``value`` to ``groups[label]`` and return ``groups``.

    When ``groups`` is omitted (or ``None``) a **fresh** dict is created, so
    independent calls never share state. When a ``groups`` dict is supplied it is
    mutated in place and returned, letting a caller accumulate across calls.
    """
    if groups is None:
        groups = {}
    groups.setdefault(label, []).append(value)
    return groups
