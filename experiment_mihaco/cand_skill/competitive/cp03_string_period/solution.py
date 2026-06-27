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
    # Edge-case guards (spec rules 4 and 5)
    if pattern == "" or len(pattern) > len(text):
        return []

    m = len(pattern)

    # Z-algorithm approach: concatenate pattern + SENTINEL + text
    # Then Z[m+1+i] >= m means a match at position i in text.
    #
    # Wildcard rule: '?' in pattern[j] (the prefix / pattern side of the Z-comparison)
    # matches any character in text (but not the sentinel '$').
    # '?' in text is treated as a literal character.
    #
    # This correctly handles all cases including overlapping matches because
    # Z-values are computed independently at each position without the
    # "guaranteed overlap" problem that plagues KMP failure functions
    # when wildcards appear at the end of the pattern.

    # Sentinel must not appear in text or pattern; we use a character
    # that cannot appear in standard str comparisons as a separator.
    # We use chr(0) (null byte) which is safe since we only compare
    # sentinel against itself (it blocks extension).
    SENTINEL = "\x00"
    s = pattern + SENTINEL + text
    n = len(s)

    # Compute Z-array with wildcard-aware comparison
    z = [0] * n
    z[0] = n
    l, r = 0, 0
    for i in range(1, n):
        if i < r:
            z[i] = min(r - i, z[i - l])
        # Extend z[i]: compare s[z[i]] (pattern pos) with s[i + z[i]]
        while i + z[i] < n:
            pc = s[z[i]]        # pattern character (prefix side)
            tc = s[i + z[i]]    # text character (suffix side)
            # '?' in pattern matches any non-sentinel character
            if pc == "?" and tc != SENTINEL:
                z[i] += 1
            elif pc == tc and pc != SENTINEL:
                # Exact match (handles literal chars in both pattern and text)
                z[i] += 1
            else:
                break
        if i + z[i] > r:
            l, r = i, i + z[i]

    # Collect match positions
    results = []
    offset = m + 1  # start of text portion in s
    for i in range(offset, n):
        if z[i] >= m:
            results.append(i - offset)
    return results


if __name__ == "__main__":
    # Smoke tests: all eight spec examples
    assert count_pattern("abcabc", "abc") == [0, 3], "Test 1 failed"
    assert count_pattern("aaaa", "aa") == [0, 1, 2], "Test 2 failed"
    assert count_pattern("abcdef", "xyz") == [], "Test 3 failed"
    assert count_pattern("abc", "abcde") == [], "Test 4 failed"
    assert count_pattern("abc", "") == [], "Test 5 failed"
    assert count_pattern("abcabc", "a?c") == [0, 3], "Test 6 failed"
    assert count_pattern("hello", "?????") == [0], "Test 7 failed"
    assert count_pattern("abcabc", "?b?") == [0, 3], "Test 8 failed"

    # Additional correctness tests
    # '?' in text is literal (only '?' in pattern is wildcard)
    assert count_pattern("a?c", "a?c") == [0], "Test 9 failed"
    assert count_pattern("a?c", "abc") == [], "Test 10 failed"

    # Overlapping wildcard matches
    assert count_pattern("aaaaa", "?a") == [0, 1, 2, 3], "Test 11 failed"
    assert count_pattern("abc", "???") == [0], "Test 12 failed"
    assert count_pattern("abcd", "??") == [0, 1, 2], "Test 13 failed"

    # Single character
    assert count_pattern("a", "a") == [0], "Test 14 failed"
    assert count_pattern("a", "b") == [], "Test 15 failed"
    assert count_pattern("a", "?") == [0], "Test 16 failed"

    # Overlapping with wildcard at end (tests failure-table-free overlap detection)
    result_17 = count_pattern("a" * 10, "a" * 4 + "?")
    assert result_17 == list(range(10 - 5 + 1)), f"Test 17 failed: {result_17}"

    # Performance gate sanity (small version)
    result_18 = count_pattern("a" * 100, "a" * 49 + "?")
    assert result_18 == list(range(100 - 50 + 1)), f"Test 18 failed: {result_18}"

    # All-wildcard pattern
    result_19 = count_pattern("abcd", "??")
    assert result_19 == [0, 1, 2], f"Test 19 failed: {result_19}"

    print("All tests passed.")
