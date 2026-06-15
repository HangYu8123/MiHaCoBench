"""Deliberately-broken reference for easy/e04_roman_ledger.

Two planted defects so the grader must catch it:
  1. to_roman uses purely ADDITIVE notation — no subtractive pairs.
     e.g. 4 -> "IIII", 9 -> "VIIII", 1994 -> "MDCCCCXCIV" (wrong).
  2. from_roman omits the canonical round-trip validation, so "IIII" is
     silently accepted as 4 instead of raising ValueError.
These MUST fail the grader (proves the grader discriminates).
"""
from __future__ import annotations

# Additive-only table (no subtractive pairs — this is the defect).
_ENCODE_TABLE: list[tuple[int, str]] = [
    (1000, "M"),
    (500,  "D"),
    (100,  "C"),
    (50,   "L"),
    (10,   "X"),
    (5,    "V"),
    (1,    "I"),
]

_VALID_CHARS = frozenset("IVXLCDM")

_DECODE = {
    "I": 1, "V": 5, "X": 10, "L": 50,
    "C": 100, "D": 500, "M": 1000,
}


def to_roman(n: int) -> str:
    """BUG: purely additive — 4->'IIII', 9->'VIIII', etc."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"n must be an int, got {type(n).__name__}")
    if n < 1 or n > 3999:
        raise ValueError(f"n={n!r} is out of range 1..3999")
    result: list[str] = []
    remainder = n
    for value, numeral in _ENCODE_TABLE:
        while remainder >= value:
            result.append(numeral)
            remainder -= value
    return "".join(result)


def from_roman(s: str) -> int:
    """BUG: no canonical-form validation — 'IIII' silently accepted as 4."""
    if not s or not isinstance(s, str):
        raise ValueError(f"Input must be a non-empty string, got {s!r}")
    s_upper = s.upper()
    if not all(c in _VALID_CHARS for c in s_upper):
        raise ValueError(f"Invalid Roman numeral string: {s!r}")

    total = 0
    prev = 0
    for ch in reversed(s_upper):
        val = _DECODE[ch]
        if val < prev:
            total -= val
        else:
            total += val
        prev = val

    if total < 1 or total > 3999:
        raise ValueError(f"Decoded value {total} out of range for input {s!r}")

    # BUG: missing round-trip check — non-canonical strings pass through.
    return total


def add_roman(a: str, b: str) -> str:
    """Add two Roman-numeral strings and return the result (uses broken to_roman)."""
    int_a = from_roman(a)
    int_b = from_roman(b)
    total = int_a + int_b
    if total > 3999:
        raise ValueError(
            f"Sum {total} exceeds the maximum value 3999"
        )
    return to_roman(total)
