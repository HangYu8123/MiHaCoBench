"""BROKEN reference for harness/h01_apportion_seats.

PLANTED DEFECT (localized): instead of the largest-remainder method (floor every
quota, then hand out the leftover seats one at a time to the largest remainders
with the documented tie-break), this version **rounds each quota independently**
with ``round(q_i)`` and returns that directly.

Consequences:
  * the result does **not** sum to ``total_seats`` whenever any leftover seats
    exist, e.g. ``apportion([34, 33, 33], 10)`` -> ``[3, 3, 3]`` (sums to 9, not
    10), because each of 3.4 / 3.3 / 3.3 rounds down,
  * there is no floor + leftover redistribution and no tie rule at all.

Cases whose quotas are already whole numbers (so independent rounding happens to
agree with the floor + zero-leftover path) still come out right — e.g.
``apportion([10, 20, 30, 40], 10) == [1, 2, 3, 4]`` — and the exception paths and
the ``total_seats == 0`` zero case are unaffected.
"""
from __future__ import annotations

from fractions import Fraction


def apportion(votes: list[int], total_seats: int) -> list[int]:
    """Allocate ``total_seats`` among parties (see TASK.md).

    Parameters
    ----------
    votes : list[int]
        Non-negative vote counts, one per party.
    total_seats : int
        Total number of seats to allocate; must be non-negative.

    Returns
    -------
    list[int]
        Seat counts in the same length and order as ``votes``.

    Raises
    ------
    ValueError
        If ``total_seats < 0``, if any vote is negative, or if there are seats to
        allocate but the total vote count is zero.
    """
    if total_seats < 0:
        raise ValueError(f"total_seats must be >= 0, got {total_seats}")
    if any(v < 0 for v in votes):
        raise ValueError("votes must all be non-negative")

    n = len(votes)
    if total_seats == 0:
        return [0] * n

    total_votes = sum(votes)
    if total_votes == 0:
        raise ValueError("cannot allocate seats when the total vote count is zero")

    quotas = [Fraction(v * total_seats, total_votes) for v in votes]
    # BUG: round each quota independently instead of floor + largest-remainder
    # top-up. The seat counts no longer sum to total_seats when leftovers exist.
    return [round(float(q)) for q in quotas]
