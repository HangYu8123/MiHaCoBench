"""
Roman numeral encoder / decoder / adder.
"""

_TO_ROMAN_TABLE = [
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


def to_roman(n: int) -> str:
    """Convert an integer to its Roman-numeral string (1 <= n <= 3999)."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"Input must be an integer, got {type(n)}")
    if n < 1 or n > 3999:
        raise ValueError(f"Input must be in range 1..3999, got {n}")
    result = []
    for value, symbol in _TO_ROMAN_TABLE:
        while n >= value:
            result.append(symbol)
            n -= value
    return "".join(result)


def from_roman(s: str) -> int:
    """Convert a Roman-numeral string to an integer.

    Raises ValueError for any string that is not exactly the output of to_roman
    for some integer in 1..3999.
    """
    if not isinstance(s, str) or not s:
        raise ValueError("Input must be a non-empty string")

    valid_chars = set("IVXLCDM")
    for ch in s:
        if ch not in valid_chars:
            raise ValueError(f"Invalid character in Roman numeral: {ch!r}")

    # Parse greedily using the same table
    original = s
    remaining = s
    total = 0
    for value, symbol in _TO_ROMAN_TABLE:
        while remaining.startswith(symbol):
            total += value
            remaining = remaining[len(symbol):]

    if remaining:
        raise ValueError(f"Malformed Roman numeral: {original!r}")

    # Validate round-trip
    if total < 1 or total > 3999:
        raise ValueError(f"Parsed value {total} is out of range 1..3999")

    if to_roman(total) != original:
        raise ValueError(f"Not a valid standard Roman numeral: {original!r}")

    return total


def add_roman(a: str, b: str) -> str:
    """Parse both Roman strings, add their values, and return the Roman encoding.

    Raises ValueError if either input is invalid or if the sum exceeds 3999.
    """
    ia = from_roman(a)
    ib = from_roman(b)
    total = ia + ib
    if total > 3999:
        raise ValueError(
            f"Sum {total} exceeds maximum representable value 3999"
        )
    return to_roman(total)
