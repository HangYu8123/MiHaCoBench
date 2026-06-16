# solution.py — Roman numeral encoder / decoder / adder
# stdlib only

_TABLE = [
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
    (100, 'C'),  (90, 'XC'), (50, 'L'),  (40, 'XL'),
    (10, 'X'),   (9, 'IX'),  (5, 'V'),   (4, 'IV'),
    (1, 'I'),
]

_VAL_MAP = {'I': 1, 'V': 5, 'X': 10, 'L': 50,
            'C': 100, 'D': 500, 'M': 1000}

_VALID_CHARS = frozenset('IVXLCDM')


def to_roman(n: int) -> str:
    """Convert integer n to a Roman-numeral string (standard subtractive notation).

    Valid range: 1 <= n <= 3999.
    Raises ValueError for any n outside this range.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"to_roman requires an integer, got {type(n).__name__!r}")
    if n < 1 or n > 3999:
        raise ValueError(f"to_roman: {n!r} is out of range [1, 3999]")
    result = ''
    for value, symbol in _TABLE:
        while n >= value:
            result += symbol
            n -= value
    return result


def from_roman(s: str) -> int:
    """Convert a Roman-numeral string to an integer.

    s must be a non-empty string of uppercase ASCII Roman characters
    (I, V, X, L, C, D, M) that forms a canonical Roman numeral in 1..3999.
    Raises ValueError for any malformed input.
    """
    if not isinstance(s, str):
        raise ValueError(f"from_roman requires a str, got {type(s).__name__!r}")
    if len(s) == 0:
        raise ValueError("from_roman: empty string is not a valid Roman numeral")
    for ch in s:
        if ch not in _VALID_CHARS:
            raise ValueError(f"from_roman: invalid character {ch!r} in {s!r}")

    # Parse with subtractive scan
    total = 0
    for i in range(len(s)):
        curr = _VAL_MAP[s[i]]
        # Look ahead: if next character exists and has a higher value, subtract current
        if i + 1 < len(s):
            nxt = _VAL_MAP[s[i + 1]]
        else:
            nxt = 0
        if curr < nxt:
            total -= curr
        else:
            total += curr

    # Round-trip validation: canonical check
    # to_roman raises ValueError if total < 1 or total > 3999 (propagates naturally)
    canonical = to_roman(total)
    if canonical != s:
        raise ValueError(
            f"from_roman: {s!r} is not a canonical Roman numeral "
            f"(canonical form of {total} is {canonical!r})"
        )
    return total


def add_roman(a: str, b: str) -> str:
    """Parse two Roman-numeral strings, add their integer values, and re-encode the sum.

    Raises ValueError if either input is invalid or if the sum exceeds 3999.
    """
    int_a = from_roman(a)   # raises ValueError for invalid a
    int_b = from_roman(b)   # raises ValueError for invalid b
    total = int_a + int_b
    # to_roman raises ValueError if total > 3999
    return to_roman(total)
