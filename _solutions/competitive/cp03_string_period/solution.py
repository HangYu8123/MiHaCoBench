"""Gold reference for competitive/cp03_string_period.

Z-algorithm-based string search supporting a single wildcard character '?'
in the pattern that matches any one character in the text.

Algorithm:
  Concatenate  S = pattern + '#' + text  and compute Z-values.
  A Z-value Z[i] gives the length of the longest prefix of S that matches S[i:].
  A match of pattern in text at position j corresponds to Z[m+1+j] >= m.

  Wildcard handling: during Z-array extension, if the reference character
  (from pattern) is '?', it matches any non-sentinel character.

Time complexity:  O(n + m) where n = len(text), m = len(pattern)
Space complexity: O(n + m) for the combined string and Z-array
"""
from __future__ import annotations


def count_pattern(text: str, pattern: str) -> list[int]:
    """Return all 0-indexed start positions where pattern occurs in text.

    Rules:
    * A literal character in pattern must match the same character in text.
    * The character '?' in pattern matches ANY single character in text.
    * Positions are returned in ascending order.
    * If pattern is empty, return [].
    * If len(pattern) > len(text), return [].

    Uses the Z-algorithm with wildcard support, giving O(n + m) time overall.
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []

    # Concatenate pattern + sentinel + text.
    # The sentinel '#' must not match '?' (we break if we hit it).
    sentinel = "#"
    combined = pattern + sentinel + text
    L = len(combined)  # = m + 1 + n

    # ------------------------------------------------------------------
    # Compute the Z-array with wildcard-aware comparison.
    # Z[i] = length of the longest prefix of combined that matches combined[i:]
    # where pattern positions with '?' match any non-sentinel character.
    # ------------------------------------------------------------------
    Z = [0] * L
    Z[0] = L  # convention: Z[0] is the full length

    left = 0   # left edge of the rightmost Z-box seen so far
    right = 0  # right edge (exclusive) of the rightmost Z-box

    for i in range(1, L):
        # Use the Z-box optimisation: if i is inside [left, right),
        # we know Z[i] >= min(right - i, Z[i - left]).
        if i < right:
            Z[i] = min(right - i, Z[i - left])

        # Extend naively from position i + Z[i].
        zi = Z[i]  # current matched length
        start = i + zi
        while start < L:
            # The separator occupies exactly index ``m``; never match across it.
            # Guarding by POSITION (not by character) keeps the algorithm correct
            # for any text/pattern characters — including a literal '#' in text.
            if start == m:
                break
            ref_idx = zi        # index into the prefix (pattern side)
            ref_ch = combined[ref_idx]
            cur_ch = combined[start]
            if ref_idx < m and ref_ch == "?":
                pass            # wildcard in pattern matches any single character
            elif ref_ch != cur_ch:
                break
            zi += 1
            start += 1

        Z[i] = zi
        if i + zi > right:
            left, right = i, i + zi

    # ------------------------------------------------------------------
    # Collect match positions: Z[m+1+j] >= m means pattern matches at j.
    # ------------------------------------------------------------------
    offset = m + 1  # index in combined where text starts
    results: list[int] = []
    for j in range(n - m + 1):
        if Z[offset + j] >= m:
            results.append(j)
    return results
