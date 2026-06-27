from fractions import Fraction
from math import floor


def apportion(votes: list[int], total_seats: int) -> list[int]:
    if total_seats < 0:
        raise ValueError("total_seats must be non-negative")
    if any(v < 0 for v in votes):
        raise ValueError("votes must be non-negative")

    V = sum(votes)

    if total_seats == 0:
        return [0] * len(votes)

    if V == 0:
        raise ValueError("sum of votes must be positive when total_seats > 0")

    n = len(votes)
    base = [0] * n
    remainders = []  # list of (remainder: Fraction, votes_i, index)

    for i, v in enumerate(votes):
        q = Fraction(v * total_seats, V)
        b = q.numerator // q.denominator  # floor of a non-negative rational
        base[i] = b
        remainders.append((q - b, v, i))

    R = total_seats - sum(base)

    # Rank: largest remainder first; tie -> larger votes first; tie -> smaller index first.
    order = sorted(
        remainders,
        key=lambda t: (t[0], t[1], -t[2]),
        reverse=True,
    )

    result = list(base)
    for k in range(R):
        idx = order[k][2]
        result[idx] += 1

    return result
