"""
Roman numeral encoder / decoder / adder.

Public contract:
    to_roman(n: int) -> str
    from_roman(s: str) -> int
    add_roman(a: str, b: str) -> str
"""

_VALS = [
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
    (100, 'C'),  (90, 'XC'), (50, 'L'),  (40, 'XL'),
    (10, 'X'),   (9, 'IX'),  (5, 'V'),   (4, 'IV'),
    (1, 'I'),
]

_CHAR = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def to_roman(n: int) -> str:
    """Convert integer n (1..3999) to a Roman-numeral string."""
    if not isinstance(n, int) or not (1 <= n <= 3999):
        raise ValueError(f"to_roman: n must be an integer in 1..3999, got {n!r}")
    result = []
    for value, symbol in _VALS:
        while n >= value:
            result.append(symbol)
            n -= value
    return ''.join(result)


def from_roman(s: str) -> int:
    """Convert a Roman-numeral string to an integer.

    Raises ValueError for any malformed input, including non-canonical forms
    such as 'IIII', 'VV', 'IC', 'IIX', etc.
    """
    if not isinstance(s, str) or len(s) == 0:
        raise ValueError("from_roman: input must be a non-empty string")

    # Validate characters
    invalid = set(s) - _CHAR.keys()
    if invalid:
        raise ValueError(
            f"from_roman: invalid character(s) {invalid!r} in {s!r}"
        )

    # Decode left-to-right using subtractive rule
    total = 0
    prev = 0
    for ch in reversed(s):
        val = _CHAR[ch]
        if val < prev:
            total -= val
        else:
            total += val
        prev = val

    # Round-trip validation: canonical strings are exactly what to_roman produces
    if total < 1 or total > 3999 or to_roman(total) != s:
        raise ValueError(
            f"from_roman: {s!r} is not a valid canonical Roman numeral"
        )

    return total


def add_roman(a: str, b: str) -> str:
    """Parse two Roman-numeral strings, add their values, and re-encode the sum.

    Raises ValueError if either input is invalid or the sum exceeds 3999.
    """
    int_a = from_roman(a)  # raises ValueError if invalid
    int_b = from_roman(b)  # raises ValueError if invalid
    total = int_a + int_b
    if total > 3999:
        raise ValueError(
            f"add_roman: sum {total} exceeds maximum Roman numeral value 3999"
        )
    return to_roman(total)
