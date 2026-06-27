"""Roman numeral encoder / decoder / adder."""

_TABLE = [
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

_VAL_MAP = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def to_roman(n: int) -> str:
    """Convert an integer in 1..3999 to its Roman-numeral string."""
    if not (1 <= n <= 3999):
        raise ValueError(f"n={n} is out of range 1..3999")
    result = ""
    for value, symbol in _TABLE:
        while n >= value:
            result += symbol
            n -= value
    return result


def from_roman(s: str) -> int:
    """Convert a Roman-numeral string to an integer.

    Raises ValueError for any malformed input, including strings that do not
    represent a valid canonical Roman numeral (as produced by to_roman).
    """
    if not s:
        raise ValueError("empty string is not a valid Roman numeral")

    # Validate all characters are in the allowed set
    for ch in s:
        if ch not in _VAL_MAP:
            raise ValueError(f"invalid character {ch!r} in Roman numeral string")

    # Parse left-to-right: subtract when current < next, otherwise add
    total = 0
    for i in range(len(s)):
        cur = _VAL_MAP[s[i]]
        if i + 1 < len(s):
            nxt = _VAL_MAP[s[i + 1]]
            if cur < nxt:
                total -= cur
            else:
                total += cur
        else:
            total += cur

    # Mandatory round-trip check: valid iff to_roman(total) == s
    # Wrap to catch ValueError from to_roman (e.g. total out of 1..3999)
    try:
        canonical = to_roman(total)
    except ValueError:
        raise ValueError(f"malformed Roman numeral string: {s!r}")

    if canonical != s:
        raise ValueError(
            f"non-canonical Roman numeral string: {s!r} "
            f"(canonical form is {canonical!r})"
        )

    return total


def add_roman(a: str, b: str) -> str:
    """Add two Roman-numeral strings and return the result as a Roman numeral.

    Raises ValueError if either input is invalid or if the sum exceeds 3999.
    """
    ia = from_roman(a)
    ib = from_roman(b)
    total = ia + ib
    if total > 3999:
        raise ValueError(
            f"sum {total} exceeds the maximum representable value of 3999"
        )
    return to_roman(total)
