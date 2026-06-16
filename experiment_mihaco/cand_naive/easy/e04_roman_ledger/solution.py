"""
Roman numeral encoder / decoder / adder.
Standard library only.
"""

_VAL_SYM = [
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

_ROMAN_CHARS = set("IVXLCDM")


def to_roman(n: int) -> str:
    """Convert integer to Roman numeral string (1 <= n <= 3999)."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"Input must be an integer, got {type(n)}")
    if n < 1 or n > 3999:
        raise ValueError(f"Input must be in range 1..3999, got {n}")

    result = []
    remaining = n
    for value, symbol in _VAL_SYM:
        while remaining >= value:
            result.append(symbol)
            remaining -= value
    return "".join(result)


def from_roman(s: str) -> int:
    """Convert Roman numeral string to integer. Raises ValueError for malformed input."""
    if not isinstance(s, str) or not s:
        raise ValueError("Input must be a non-empty string")

    # Check all characters are valid Roman numeral characters
    for ch in s:
        if ch not in _ROMAN_CHARS:
            raise ValueError(f"Invalid character '{ch}' in Roman numeral string")

    # Parse the Roman numeral by scanning left to right
    # Use standard subtractive notation parsing
    roman_values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

    total = 0
    prev = 0
    for ch in reversed(s):
        val = roman_values[ch]
        if val < prev:
            total -= val
        else:
            total += val
        prev = val

    # Validate by round-tripping through to_roman
    if total < 1 or total > 3999:
        raise ValueError(f"Roman numeral '{s}' represents out-of-range value {total}")

    canonical = to_roman(total)
    if canonical != s:
        raise ValueError(
            f"Malformed Roman numeral '{s}': canonical form is '{canonical}'"
        )

    return total


def add_roman(a: str, b: str) -> str:
    """Add two Roman numeral strings and return the result as a Roman numeral string."""
    val_a = from_roman(a)
    val_b = from_roman(b)
    total = val_a + val_b
    if total > 3999:
        raise ValueError(
            f"Sum {total} exceeds maximum representable value 3999 in Roman numerals"
        )
    return to_roman(total)
