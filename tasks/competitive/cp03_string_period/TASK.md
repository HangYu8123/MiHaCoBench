# Competitive 03 — `count_pattern`: KMP String Search with Wildcard

**Created:** 2026-06-15 · **Category:** competitive · **Weight:** 8

Implement a **single file** `solution.py` (standard library only) that finds all
occurrences of a pattern inside a text, where the pattern may contain a single
wildcard character `'?'` that matches any one character.

## Public contract

```python
def count_pattern(text: str, pattern: str) -> list[int]:
    """Return all 0-indexed start positions where pattern occurs in text.

    Rules:
    * A literal character in pattern must match the same character in text.
    * The character '?' in pattern matches ANY single character in text.
    * Positions are returned in ascending order.
    * If pattern is empty, return [] (no match for empty pattern).
    * If len(pattern) > len(text), return [].

    Parameters
    ----------
    text    : str  — the text to search
    pattern : str  — the pattern to find (may contain '?' wildcards)

    Returns
    -------
    list[int] — sorted list of 0-indexed starting positions of all matches
    """
```

### Constraints

* `0 ≤ len(text) ≤ 1 000 000`
* `0 ≤ len(pattern) ≤ len(text)`
* The character `'?'` in the **pattern only** is a wildcard matching any single character
* `'?'` in the **text** is treated as a literal character (only the pattern has wildcards)
* Returns a plain Python `list[int]`

## Complexity requirements (hard-gated in the grader)

| Requirement | Detail |
|---|---|
| **Time** | O(n + m) — where n = len(text), m = len(pattern). A naïve O(n · m) substring scan **will time out** on the adversarial input below. |

### Concrete gate values (in the grader)

* **Hard time gate:** `text = 'a' * 1_000_000`, `pattern = 'a' * 499 + '?'` —
  must complete within **5 seconds**.
  A naïve O(n · m) scan performs ~5 × 10¹¹ comparisons on this input and times
  out; a KMP or Z-algorithm solution finishes in under 1 second.

## Implementation note (informative, not required)

Two standard linear-time approaches work:

1. **KMP (Knuth-Morris-Pratt)**: Build a failure function over the pattern
   (treating `'?'` as matching any character in the match step), then scan text
   left-to-right without backtracking.
2. **Z-algorithm**: Concatenate `pattern + '$' + text`, compute Z-values, and
   identify positions where `Z[m + 1 + i] >= m` (treating `'?'` matches suitably).

## Examples

```python
count_pattern("abcabc", "abc")     == [0, 3]
count_pattern("aaaa", "aa")        == [0, 1, 2]   # overlapping matches
count_pattern("abcdef", "xyz")     == []           # no match
count_pattern("abc", "abcde")      == []           # pattern longer than text
count_pattern("abc", "")           == []           # empty pattern → []
count_pattern("abcabc", "a?c")     == [0, 3]       # '?' matches 'b'
count_pattern("hello", "?????")    == [0]          # all-wildcard of same length
count_pattern("abcabc", "?b?")     == [0, 3]       # wildcard at start and end
```
