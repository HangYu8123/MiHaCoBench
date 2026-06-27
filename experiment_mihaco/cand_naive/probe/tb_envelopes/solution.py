import bisect


def max_nested(boxes: list[tuple[int, int]]) -> int:
    if not boxes:
        return 0
    ordered = sorted(boxes, key=lambda b: (b[0], -b[1]))
    tails: list[int] = []
    for _, h in ordered:
        i = bisect.bisect_left(tails, h)
        if i == len(tails):
            tails.append(h)
        else:
            tails[i] = h
    return len(tails)
