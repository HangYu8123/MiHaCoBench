"""
Range Update / Range Sum using Dual Fenwick BIT.

Maintains two BITs (B1, B2) such that:
  prefix_sum(i) = B1.query(i+1) * (i+1) - B2.query(i+1)

Range add [l, r] += v:
  B1 update l+1 with +v, r+2 with -v
  B2 update l+1 with +v*l, r+2 with -v*(r+1)

Range sum [l, r]:
  = prefix_sum(r) - prefix_sum(l-1)
"""


def process_queries(n: int, ops: list[tuple]) -> list[int]:
    """Process a sequence of range operations on an array of n zeros.

    Each element of ops is one of:
      ("add", l, r, v)  — add integer v to every index in [l, r] inclusive (0-indexed)
      ("sum", l, r)     — return the current sum of elements at indices [l, r] inclusive

    Return a list of integers: one result per "sum" operation, in order.

    Parameters
    ----------
    n   : int   — length of the array; indices are 0-indexed: [0, n-1]
    ops : list  — list of operation tuples as described above

    Returns
    -------
    list[int]   — results of all "sum" queries, in the order they appear in ops
    """
    # BIT size is n+2 to handle boundary updates safely
    size = n + 2
    b1 = [0] * (size + 1)
    b2 = [0] * (size + 1)

    def bit_update(tree, i, delta):
        while i <= size:
            tree[i] += delta
            i += i & (-i)

    def bit_query(tree, i):
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s

    def range_add(l, r, v):
        # l, r are 0-indexed; convert to 1-indexed for BIT
        l1 = l + 1
        r1 = r + 1
        bit_update(b1, l1, v)
        bit_update(b1, r1 + 1, -v)
        bit_update(b2, l1, v * (l1 - 1))
        bit_update(b2, r1 + 1, -v * r1)

    def prefix_sum(i):
        # prefix sum from index 0 to i (0-indexed)
        # = B1.query(i+1) * (i+1) - B2.query(i+1)
        i1 = i + 1
        return bit_query(b1, i1) * i1 - bit_query(b2, i1)

    def range_sum(l, r):
        res = prefix_sum(r)
        if l > 0:
            res -= prefix_sum(l - 1)
        return res

    results = []
    for op in ops:
        if op[0] == "add":
            _, l, r, v = op
            range_add(l, r, v)
        else:  # "sum"
            _, l, r = op
            results.append(range_sum(l, r))

    return results
