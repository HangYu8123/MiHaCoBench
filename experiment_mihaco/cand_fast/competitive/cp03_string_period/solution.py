def count_pattern(text: str, pattern: str) -> list[int]:
    """Return all 0-indexed start positions where pattern occurs in text.

    Rules:
    * A literal character in pattern must match the same character in text.
    * The character '?' in pattern matches ANY single character in text.
    * Positions are returned in ascending order.
    * If pattern is empty, return [] (no match for empty pattern).
    * If len(pattern) > len(text), return [].
    """
    n = len(text)
    m = len(pattern)

    if m == 0 or m > n:
        return []

    # Build KMP failure (LPS) array with one-sided wildcard handling.
    #
    # In the LPS self-comparison, pattern[length] is the "pattern" (prefix) side
    # and pattern[i] is the "text" (suffix) side.  Wildcards are asymmetric: only
    # the prefix/pattern side ('?' at position `length`) counts as a wildcard that
    # matches any character; the suffix side is treated as a literal.  This mirrors
    # the asymmetric search-phase comparison and prevents spurious overlaps (e.g.
    # '?b?' incorrectly matching at non-boundaries if both sides were wildcard).
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[length] == '?' or pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1

    # KMP search phase.
    # Comparison is asymmetric: '?' in pattern matches any char in text,
    # but '?' in text is a literal character.
    results = []
    j = 0  # current position in pattern
    for i in range(n):
        # Fall back while mismatch
        while j > 0 and not (pattern[j] == '?' or pattern[j] == text[i]):
            j = lps[j - 1]
        if pattern[j] == '?' or pattern[j] == text[i]:
            j += 1
        if j == m:
            results.append(i - m + 1)
            j = lps[j - 1]

    return results
