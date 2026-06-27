"""Gold reference for harness/h02_merge_intervals.

Coalesce a list of HALF-OPEN integer intervals ``[start, end)`` into the minimal
list of disjoint half-open intervals covering exactly the same point set, sorted
by ``start`` ascending.

The subtlety is entirely in the half-open semantics:

  * Two intervals coalesce iff the later one's ``start`` is ``<=`` the running
    end (NOT strictly ``<``). Because the intervals are half-open, ``[1, 3)`` and
    ``[3, 5)`` are contiguous — their union is exactly ``[1, 5)`` with no gap and
    no overlap — so they MUST merge.
  * A zero-length interval ``start == end`` covers no points at all; it is
    dropped and never bridges a gap.
  * ``start > end`` (strictly) is invalid and raises ``ValueError``.

The function is pure: it never mutates the input list or its tuples.
"""
from __future__ import annotations


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the minimal disjoint half-open cover of ``intervals``.

    Each input ``(start, end)`` is a half-open interval ``[start, end)`` covering
    every point ``x`` with ``start <= x < end``. The result is the minimal list
    of disjoint half-open intervals covering exactly the same point set, sorted by
    ``start`` ascending and returned as ``(int, int)`` tuples.

    Rules
    -----
    * Half-open adjacency merges: two intervals coalesce iff the later one's
      ``start`` is ``<=`` the running end (so ``[1, 3)`` and ``[3, 5)`` become
      ``[1, 5)``).
    * A zero-length interval (``start == end``) covers no points and is dropped;
      it never appears in the output and never bridges a gap.
    * The input may be empty, unsorted, duplicated, nested, and contain negative
      coordinates.

    Parameters
    ----------
    intervals : list[tuple[int, int]]
        The half-open intervals to coalesce. Not mutated.

    Returns
    -------
    list[tuple[int, int]]
        The minimal disjoint cover, sorted by ``start`` ascending.

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

    # Sort by (start, end); a stable sort keeps the result deterministic.
    cleaned.sort()

    merged: list[tuple[int, int]] = []
    cur_start, cur_end = cleaned[0]
    for start, end in cleaned[1:]:
        if start <= cur_end:
            # Contiguous or overlapping (half-open adjacency): extend the run.
            if end > cur_end:
                cur_end = end
        else:
            # A genuine gap (start strictly past the running end): close the run.
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end
    merged.append((cur_start, cur_end))
    return merged
