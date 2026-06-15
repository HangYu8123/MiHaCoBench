"""Gold reference for easy/e04_roman_ledger — Roman numeral encoder / decoder / adder."""
from __future__ import annotations

# Mapping table in descending order (subtractive notation included).
_ENCODE_TABLE: list[tuple[int, str]] = [
    (1000, "M"),
    (900,  "CM"),
    (500,  "D"),
    (400,  "CD"),
    (100,  "C"),
    (90,   "XC"),
    (50,   "L"),
    (40,   "XL"),
    (10,   "X"),
    (9,    "IX"),
    (5,    "V"),
    (4,    "IV"),
    (1,    "I"),
]

_VALID_CHARS = frozenset("IVXLCDM")


def to_roman(n: int) -> str:
    """Convert integer *n* (1..3999) to a Roman-numeral string (subtractive notation).

    Raises ValueError if n is outside the valid range.
    """
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
    """Convert Roman-numeral string *s* to an integer.

    Raises ValueError if *s* is not a valid subtractive-notation Roman numeral
    in the range 1..3999.
    """
    if not s or not isinstance(s, str):
        raise ValueError(f"Input must be a non-empty string, got {s!r}")
    s_upper = s.upper()
    if not all(c in _VALID_CHARS for c in s_upper):
        raise ValueError(f"Invalid Roman numeral string: {s!r}")

    # Parse value using the standard greedy decoding.
    _DECODE = {
        "I": 1, "V": 5, "X": 10, "L": 50,
        "C": 100, "D": 500, "M": 1000,
    }
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
        raise ValueError(f"Decoded value {total} out of range 1..3999 for input {s!r}")

    # Validate by re-encoding: only canonical subtractive-notation strings are accepted.
    if to_roman(total) != s_upper:
        raise ValueError(
            f"{s!r} is not a valid canonical Roman numeral (expected {to_roman(total)!r})"
        )
    return total


def add_roman(a: str, b: str) -> str:
    """Add two Roman-numeral strings and return the result as a Roman numeral.

    Raises ValueError if either input is invalid or if the sum exceeds 3999.
    """
    int_a = from_roman(a)   # propagates ValueError for bad input
    int_b = from_roman(b)
    total = int_a + int_b
    if total > 3999:
        raise ValueError(
            f"Sum {total} (from {a!r} + {b!r}) exceeds the maximum value 3999"
        )
    return to_roman(total)
