def process_queries(n: int, ops: list[tuple]) -> list[int]:
    """Process a sequence of range operations on an array of n zeros.

    Each element of ops is one of:
      ("add", l, r, v)  -- add integer v to every index in [l, r] inclusive (0-indexed)
      ("sum", l, r)     -- return the current sum of elements at indices [l, r] inclusive

    Return a list of integers: one result per "sum" operation, in order.

    Parameters
    ----------
    n   : int   -- length of the array; indices are 0-indexed: [0, n-1]
    ops : list  -- list of operation tuples as described above

    Returns
    -------
    list[int]   -- results of all "sum" queries, in the order they appear in ops
    """
    # Dual Fenwick BIT approach:
    # For 0-indexed array of size n, maintain two BITs B1 and B2 (1-indexed internally, size n+2).
    # Range add [l, r, v]:
    #   B1: point_add(l+1, v), point_add(r+2, -v)
    #   B2: point_add(l+1, v*l), point_add(r+2, -v*(r+1))
    # Prefix sum [0..i] = B1.query(i+1) * (i+1) - B2.query(i+1)
    #   where i is 0-based and (i+1) is used as the multiplier (not i).
    # Range sum [l, r] = prefix(r) - (prefix(l-1) if l > 0 else 0)

    B1 = [0] * (n + 2)
    B2 = [0] * (n + 2)

    def bit_add(tree, i, v):
        # 1-indexed BIT update: add v at position i
        while i <= n:
            tree[i] += v
            i += i & (-i)

    def bit_query(tree, i):
        # 1-indexed BIT prefix query: sum from 1..i
        # Returns 0 if i <= 0 (loop condition handles i==0 naturally)
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s

    def prefix(i):
        # Prefix sum of array[0..i] (0-based i)
        # Internally queries at (i+1), multiplier is (i+1) — not i
        ip1 = i + 1  # 1-based internal index
        return bit_query(B1, ip1) * ip1 - bit_query(B2, ip1)

    results = []

    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            # Update B1: range add using difference array
            bit_add(B1, l + 1, v)
            bit_add(B1, r + 2, -v)
            # Update B2: using corrected 0-indexed formula
            # point_add at l+1: v*l, point_add at r+2: -v*(r+1)
            bit_add(B2, l + 1, v * l)
            bit_add(B2, r + 2, -v * (r + 1))
        elif op[0] == "sum":
            _, l, r = op
            # Range sum [l, r] = prefix(r) - prefix(l-1)
            # Guard: if l == 0, prefix(-1) = 0
            right = prefix(r)
            left = prefix(l - 1) if l > 0 else 0
            results.append(right - left)

    return results
