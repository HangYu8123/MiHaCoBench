"""
Roman numeral encoder / decoder / adder.

Public contract:
    to_roman(n: int) -> str
    from_roman(s: str) -> int
    add_roman(a: str, b: str) -> str
"""

# Ordered (descending) list of (value, symbol) pairs for greedy encoding.
_TO_ROMAN_TABLE = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]

# Map from Roman character to its base value.
_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

# Set of valid Roman characters.
_VALID_CHARS = frozenset(_ROMAN_VALUES.keys())


def to_roman(n: int) -> str:
    """Convert an integer to a Roman-numeral string.

    Args:
        n: An integer in the range 1..3999 (inclusive).

    Returns:
        The standard subtractive Roman-numeral representation.

    Raises:
        ValueError: If n is not an integer or is outside 1..3999.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"n must be an int, got {type(n).__name__}")
    if n < 1 or n > 3999:
        raise ValueError(f"n must be in range 1..3999, got {n}")

    result = []
    remaining = n
    for value, symbol in _TO_ROMAN_TABLE:
        while remaining >= value:
            result.append(symbol)
            remaining -= value
    return "".join(result)


def from_roman(s: str) -> int:
    """Convert a Roman-numeral string to an integer.

    Validity is defined strictly as: to_roman(from_roman(s)) == s.
    Any string that does not satisfy this round-trip is rejected.

    Args:
        s: A non-empty string of uppercase Roman characters (I V X L C D M).

    Returns:
        The integer value corresponding to the Roman numeral.

    Raises:
        ValueError: If s is empty, contains invalid characters, or does not
                    represent a valid standard Roman numeral.
    """
    if not isinstance(s, str):
        raise ValueError(f"s must be a str, got {type(s).__name__}")
    if len(s) == 0:
        raise ValueError("Empty string is not a valid Roman numeral")
    # Validate character set — must be uppercase Roman letters only.
    invalid = set(s) - _VALID_CHARS
    if invalid:
        raise ValueError(
            f"Invalid character(s) in Roman numeral string: {sorted(invalid)}"
        )

    # Parse left-to-right using the standard subtractive rule:
    # if current value < next value, subtract current; otherwise add current.
    total = 0
    for i, ch in enumerate(s):
        cur_val = _ROMAN_VALUES[ch]
        if i + 1 < len(s):
            next_val = _ROMAN_VALUES[s[i + 1]]
            if cur_val < next_val:
                total -= cur_val
            else:
                total += cur_val
        else:
            total += cur_val

    # Round-trip validation: a valid Roman numeral must survive the round-trip.
    if total < 1 or total > 3999 or to_roman(total) != s:
        raise ValueError(f"'{s}' is not a valid standard Roman numeral")

    return total


def add_roman(a: str, b: str) -> str:
    """Add two Roman-numeral strings and return their sum as a Roman numeral.

    Args:
        a: A valid Roman-numeral string.
        b: A valid Roman-numeral string.

    Returns:
        The Roman-numeral encoding of (value(a) + value(b)).

    Raises:
        ValueError: If either a or b is not a valid Roman numeral, or if the
                    sum exceeds 3999.
    """
    # Let from_roman propagate ValueError for invalid inputs.
    val_a = from_roman(a)
    val_b = from_roman(b)
    total = val_a + val_b
    if total > 3999:
        raise ValueError(
            f"Sum {total} exceeds maximum Roman numeral value 3999 "
            f"(from '{a}' + '{b}')"
        )
    # total >= 2 (both inputs are >= 1), so to_roman is always valid here.
    return to_roman(total)
