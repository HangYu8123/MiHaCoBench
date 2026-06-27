"""Grader for harness/h01_apportion_seats.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference rounds each quota independently with ``round(q_i)`` instead
of doing floor + largest-remainder leftover distribution, so its result does NOT
sum to ``total_seats`` whenever leftover seats exist (e.g. ``[34,33,33],10`` ->
``[3,3,3]``). The shape/sum invariant, the worked examples, the tie cases, and
the independent-oracle test catch this; the exact-quota happy path, the
``total_seats == 0`` case, and the exception paths still pass on the broken
variant.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h01_apportion_seats"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

apportion = gu.load_callable(SOL, "solution.py", "apportion")


# ---------------------------------------------------------------------------
# Independent oracle: a structurally-different exact Hamilton implementation.
#
# It does NOT import the gold. It computes each remainder as an exact Fraction
# and then distributes the leftover seats with an explicit "pick the current
# best party, award one seat, repeat" loop (greedy, one seat at a time) rather
# than the gold's single sorted() over a composite key. The selection key is
# (remainder DESC, votes DESC, index ASC), evaluated with exact Fraction
# comparisons so no float tie is mis-ordered.
# ---------------------------------------------------------------------------
def _oracle(votes: list[int], total_seats: int) -> list[int]:
    if total_seats < 0:
        raise ValueError("total_seats < 0")
    if any(v < 0 for v in votes):
        raise ValueError("negative vote")
    n = len(votes)
    if total_seats == 0:
        return [0] * n
    total_votes = sum(votes)
    if total_votes == 0:
        raise ValueError("zero total votes with seats to allocate")

    quotas = [Fraction(v * total_seats, total_votes) for v in votes]
    seats = [int(q // 1) for q in quotas]            # floor of each exact quota
    remainders = [quotas[i] - seats[i] for i in range(n)]
    leftover = total_seats - sum(seats)

    # Award leftover seats one at a time to the current best-ranked party.
    awarded: set[int] = set()
    for _ in range(leftover):
        best = None
        for i in range(n):
            if i in awarded:
                continue
            key = (remainders[i], votes[i], -i)  # maximise: bigger remainder, bigger votes, smaller index
            if best is None or key > best[0]:
                best = (key, i)
        seats[best[1]] += 1
        awarded.add(best[1])
    return seats


# Deterministic, committed (votes, total_seats) cases for the oracle test. They
# span: a leftover-by-largest-remainder case, an all-tied case, an exact-quota
# case, a tie broken by votes, a 0-vote party, a single party, and a couple of
# larger mixes that exercise multiple leftover seats.
_ORACLE_CASES = [
    ([34, 33, 33], 10),
    ([1, 1, 1], 2),
    ([10, 20, 30, 40], 10),
    ([1, 1, 4], 4),
    ([5, 0, 5], 3),
    ([7], 4),
    ([100, 50, 25, 25], 8),
    ([1, 2, 3, 4, 5], 7),
    ([60, 30, 10], 5),
    ([1, 1, 1, 1, 1, 1], 4),
    ([0, 0, 7], 3),
    ([41, 39, 20], 15),
]


# ---------------------------------------------------------------------------
# Test 1 [FAIL_TO_PASS]: headline invariant — output length == len(votes) AND
# sum(result) == total_seats for MANY committed cases. The independent-rounding
# bug violates the sum whenever leftover seats exist.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("votes,total_seats", _ORACLE_CASES + [
    ([34, 33, 33], 7),
    ([3, 3, 3, 1], 6),
    ([2, 2, 2], 4),
    ([9, 8, 7, 6, 5], 11),
])
def test_shape_and_sum_invariant(votes, total_seats):
    result = apportion(list(votes), total_seats)
    assert isinstance(result, list)
    assert len(result) == len(votes)
    assert all(isinstance(x, int) for x in result)
    assert all(x >= 0 for x in result)
    assert sum(result) == total_seats


# ---------------------------------------------------------------------------
# Test 2: worked example — leftover seat goes to the largest remainder.
# ---------------------------------------------------------------------------
def test_worked_largest_remainder():
    assert apportion([34, 33, 33], 10) == [4, 3, 3]


# ---------------------------------------------------------------------------
# Test 3 [FAIL_TO_PASS]: worked example — all-tied remainders, equal votes, so
# the leftover seats go by smaller index.
# ---------------------------------------------------------------------------
def test_worked_tie_by_index():
    assert apportion([1, 1, 1], 2) == [1, 1, 0]


# ---------------------------------------------------------------------------
# Test 4: worked example — exact quotas, no leftover seats (the happy path).
# ---------------------------------------------------------------------------
def test_worked_exact_quota_happy_path():
    assert apportion([10, 20, 30, 40], 10) == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Test 5 [FAIL_TO_PASS]: worked example — tied remainders broken by larger
# votes first, then by index.
# ---------------------------------------------------------------------------
def test_worked_tie_by_votes_then_index():
    assert apportion([1, 1, 4], 4) == [1, 0, 3]


# ---------------------------------------------------------------------------
# Test 6: a 0-vote party gets 0 seats when no leftover reaches it.
# ---------------------------------------------------------------------------
def test_zero_vote_party_gets_no_seats():
    # quotas 4.5, 0, 4.5 -> base [4,0,4], one leftover; remainders 0.5,0,0.5;
    # tie between parties 0 and 2 broken by votes (equal) then index -> party 0.
    result = apportion([5, 0, 5], 3)
    assert result == [2, 0, 1]
    assert sum(result) == 3
    assert result[1] == 0


# ---------------------------------------------------------------------------
# Test 7: a 0-vote party CAN receive a leftover seat only via the tie-break,
# but never when its remainder is strictly smaller than a contender's.
# ---------------------------------------------------------------------------
def test_zero_vote_party_excluded_when_remainder_smaller():
    # votes [0,0,7], 3 seats: V=7, quotas 0,0,3 -> base [0,0,3], sum 3, no
    # leftover. The 0-vote parties stay at 0.
    assert apportion([0, 0, 7], 3) == [0, 0, 3]


# ---------------------------------------------------------------------------
# Test 8 [FAIL_TO_PASS]: independent-oracle agreement on every committed case,
# plus the sum invariant. Expected values come from _oracle (above), NOT from
# the gold solution.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("votes,total_seats", _ORACLE_CASES)
def test_matches_independent_oracle(votes, total_seats):
    expected = _oracle(list(votes), total_seats)
    got = apportion(list(votes), total_seats)
    assert got == expected, f"votes={votes} seats={total_seats}: {got} != oracle {expected}"
    assert sum(got) == total_seats


# ---------------------------------------------------------------------------
# Test 9: total_seats == 0 returns all-zeros of the right length (NOT an error),
# including the empty-votes edge case.
# ---------------------------------------------------------------------------
def test_zero_seats_returns_zeros():
    assert apportion([5, 3, 2], 0) == [0, 0, 0]
    assert apportion([], 0) == []
    assert apportion([0, 0, 0], 0) == [0, 0, 0]


# ---------------------------------------------------------------------------
# Test 10: exception contract — assert the TYPE only.
# ---------------------------------------------------------------------------
def test_negative_total_seats_raises():
    with pytest.raises(ValueError):
        apportion([1, 2, 3], -1)


def test_negative_vote_raises():
    with pytest.raises(ValueError):
        apportion([1, -2, 3], 5)


def test_seats_but_zero_total_votes_raises():
    with pytest.raises(ValueError):
        apportion([0, 0, 0], 5)


def test_seats_but_empty_votes_raises():
    with pytest.raises(ValueError):
        apportion([], 5)


# ---------------------------------------------------------------------------
# Test 11: purity — the input list is not mutated.
# ---------------------------------------------------------------------------
def test_does_not_mutate_input():
    votes = [34, 33, 33]
    before = list(votes)
    apportion(votes, 10)
    assert votes == before


# ---------------------------------------------------------------------------
# Test 12: a single party takes every seat.
# ---------------------------------------------------------------------------
def test_single_party_takes_all_seats():
    assert apportion([7], 4) == [4]
    assert apportion([1], 0) == [0]


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail).
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
