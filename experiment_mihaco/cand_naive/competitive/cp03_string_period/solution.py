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
    n = len(text)
    m = len(pattern)

    if m == 0 or m > n:
        return []

    # Build KMP failure function for the pattern.
    # When building the failure function, '?' in the pattern matches any char,
    # so we treat two pattern characters as "equal" if either is '?' or they
    # are the same literal character.
    def chars_match(pc: str, tc: str) -> bool:
        """Return True if pattern char pc matches text/pattern char tc."""
        return pc == '?' or tc == '?' or pc == tc

    # Build failure function (partial match table) for pattern.
    # fail[i] = length of longest proper prefix of pattern[:i+1] that is also
    # a suffix, using wildcard-aware matching.
    fail = [0] * m
    k = 0
    for i in range(1, m):
        # Shrink k while pattern[k] doesn't match pattern[i]
        while k > 0 and not chars_match(pattern[k], pattern[i]):
            k = fail[k - 1]
        if chars_match(pattern[k], pattern[i]):
            k += 1
        fail[i] = k

    # KMP search
    results = []
    k = 0  # number of pattern characters matched so far
    for i in range(n):
        # Shrink k while pattern[k] doesn't match text[i]
        while k > 0 and not chars_match(pattern[k], text[i]):
            k = fail[k - 1]
        if chars_match(pattern[k], text[i]):
            k += 1
        if k == m:
            results.append(i - m + 1)
            k = fail[k - 1]

    return results
