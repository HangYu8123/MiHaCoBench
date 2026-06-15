# Easy 04 — `roman_ledger`: Roman numeral encoder / decoder / adder

**Created:** 2026-06-15 · **Category:** easy · **Weight:** 1

Implement three Roman-numeral utilities in a single `solution.py` file.
Use the **standard library only** — no third-party packages.

## Public contract (must match exactly)

```python
def to_roman(n: int) -> str:
    ...

def from_roman(s: str) -> int:
    ...

def add_roman(a: str, b: str) -> str:
    ...
```

### `to_roman(n: int) -> str`

Convert an integer to its Roman-numeral string using **standard subtractive
notation**.

* Valid input range: **1 ≤ n ≤ 3999**.
* Raise `ValueError` for any `n` outside this range (including 0 and negative
  numbers, and numbers ≥ 4000).
* Use the following subtractive pairs (required):

  | Value | Symbol |
  |-------|--------|
  | 1000  | M      |
  | 900   | CM     |
  | 500   | D      |
  | 400   | CD     |
  | 100   | C      |
  | 90    | XC     |
  | 50    | L      |
  | 40    | XL     |
  | 10    | X      |
  | 9     | IX     |
  | 5     | V      |
  | 4     | IV     |
  | 1     | I      |

  Examples: 4 → `"IV"`, 9 → `"IX"`, 1994 → `"MCMXCIV"`, 3999 → `"MMMCMXCIX"`.

### `from_roman(s: str) -> int`

Convert a Roman-numeral string to an integer.

* `s` must be a non-empty string of uppercase ASCII Roman characters.
* Raise `ValueError` for any malformed input, including:
  * Strings containing characters other than `I V X L C D M`.
  * The empty string.
  * Strings that do not obey standard subtractive notation (e.g. `"IIII"`,
    `"VV"`, `"IIX"`, `"IC"` — any string for which `to_roman(from_roman_value)`
    ≠ the original string is malformed).
* A valid Roman string is exactly the output `to_roman` would produce for some
  integer in 1..3999. Any other string raises `ValueError`.

### `add_roman(a: str, b: str) -> str`

Parse both Roman strings, add their integer values, and re-encode the sum.

* Raise `ValueError` if either input is invalid (not a legal Roman numeral).
* Raise `ValueError` if the integer sum exceeds 3999.
* Return a Roman-numeral string (the encoding of the sum).

## Notes

* Determinism: identical input ⇒ identical output.
* The grader only imports `to_roman`, `from_roman`, and `add_roman` by name.
* No command-line interface is required.
