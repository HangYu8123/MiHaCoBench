"""Gold reference for harness/h01_apportion_seats.

Largest-remainder (Hamilton / Hare-Niemeyer) seat apportionment.

Seats are allocated in proportion to votes:

  1. exact quota q_i = votes_i * total_seats / V   (V = sum(votes)),
  2. each party gets base_i = floor(q_i),
  3. R = total_seats - sum(base_i) leftover seats remain,
  4. the R parties with the largest fractional remainder r_i = q_i - base_i each
     get one extra seat,
  5. ties on r_i are broken by larger votes_i, then by smaller index.

All comparisons use ``fractions.Fraction`` so the ordering is exact: no
floating-point error can ever mis-rank an exact remainder tie. The returned list
has the same length and order as ``votes`` and sums to exactly ``total_seats``.
"""
from __future__ import annotations

from fractions import Fraction


def apportion(votes: list[int], total_seats: int) -> list[int]:
    """Allocate ``total_seats`` among parties by the largest-remainder method.

    Parameters
    ----------
    votes : list[int]
        Non-negative vote counts, one per party.
    total_seats : int
        Total number of seats to allocate; must be non-negative.

    Returns
    -------
    list[int]
        Seat counts in the same length and order as ``votes``; sums to exactly
        ``total_seats``.

    Raises
    ------
    ValueError
        If ``total_seats < 0``, if any vote is negative, or if there are seats to
        allocate (``total_seats > 0``) but the total vote count is zero
        (including an empty ``votes``).
    """
    if total_seats < 0:
        raise ValueError(f"total_seats must be >= 0, got {total_seats}")
    if any(v < 0 for v in votes):
        raise ValueError("votes must all be non-negative")

    n = len(votes)
    # total_seats == 0 is always valid: nobody gets a seat (works for empty votes).
    if total_seats == 0:
        return [0] * n

    total_votes = sum(votes)
    if total_votes == 0:
        raise ValueError("cannot allocate seats when the total vote count is zero")

    # Exact quota and its floor for each party.
    quotas = [Fraction(v * total_seats, total_votes) for v in votes]
    base = [q.numerator // q.denominator for q in quotas]  # exact floor of a Fraction
    seats = list(base)

    leftover = total_seats - sum(base)  # number of one-seat top-ups to distribute

    # Rank parties for the leftover seats: largest remainder first, then larger
    # votes, then smaller index. Sorting ascending on the negated keys keeps the
    # comparison exact (Fraction for the remainder, int for votes).
    remainders = [q - b for q, b in zip(quotas, base)]
    order = sorted(
        range(n),
        key=lambda i: (-remainders[i], -votes[i], i),
    )
    for i in order[:leftover]:
        seats[i] += 1

    return seats
