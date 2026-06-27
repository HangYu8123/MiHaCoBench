def edit_distance(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between strings a and b.

    Each insertion, deletion, or substitution costs 1.
    """
    # Swap so that b is the shorter string — column array size is min(m,n)+1.
    if len(a) < len(b):
        a, b = b, a

    m, n = len(a), len(b)

    # Base case: distance from "" to b[0..j] = j
    prev = list(range(n + 1))

    for i in range(1, m + 1):
        # Save prev[0] (= i-1) as the diagonal before overwriting prev[0].
        diag = prev[0]
        prev[0] = i  # distance from a[0..i] to "" is i

        for j in range(1, n + 1):
            # Save prev[j] ("cell above") before overwriting — becomes next diag.
            temp = prev[j]
            if a[i - 1] == b[j - 1]:
                # Characters match: no edit needed, take diagonal cost.
                prev[j] = diag
            else:
                # diag = substitute, temp = delete, prev[j-1] = insert
                prev[j] = 1 + min(diag, temp, prev[j - 1])
            # Advance diagonal for next column.
            diag = temp

    return prev[n]
