"""BROKEN reference for harness/h02_merge_intervals.

PLANTED DEFECT (localized): the merge test uses STRICT overlap (``start <
cur_end``) instead of the half-open adjacency rule (``start <= cur_end``). So
genuinely *overlapping* intervals still coalesce, but *adjacent* half-open
intervals do NOT: ``[1, 3)`` and ``[3, 5)`` are wrongly left as two intervals
``[(1, 3), (3, 5)]`` instead of the single ``[(1, 5)]`` their union actually is.

Everything else is correct: zero-length intervals are still dropped, the
``start > end`` ValueError still fires, sorting/purity are intact. ONLY the
adjacency rule is broken, so the happy path of overlapping/nested inputs still
passes while the adjacency and chain tests fail.
"""
from __future__ import annotations


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the (intended) minimal disjoint half-open cover of ``intervals``.

    See TASK.md for the full contract. (This variant mis-handles half-open
    adjacency — see the module docstring.)

    Raises
    ------
    ValueError
        If any interval has ``start > end`` (strictly).
    """
    # Validate and drop zero-length (empty) intervals without mutating the input.
    cleaned: list[tuple[int, int]] = []
    for start, end in intervals:
        if start > end:
            raise ValueError(f"interval start > end: ({start}, {end})")
        if start == end:
            # Zero-length interval covers no points — drop it entirely.
            continue
        cleaned.append((int(start), int(end)))

    if not cleaned:
        return []

    cleaned.sort()

    merged: list[tuple[int, int]] = []
    cur_start, cur_end = cleaned[0]
    for start, end in cleaned[1:]:
        # BUG: strict overlap (<) — adjacent half-open intervals ([1,3) & [3,5))
        # are NOT coalesced even though their union has no gap.
        if start < cur_end:
            if end > cur_end:
                cur_end = end
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end
    merged.append((cur_start, cur_end))
    return merged
