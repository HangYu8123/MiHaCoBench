def is_match(pattern: str, text: str) -> bool:
    if "**" in pattern:
        collapsed = []
        prev_star = False
        for ch in pattern:
            if ch == "*":
                if prev_star:
                    continue
                prev_star = True
            else:
                prev_star = False
            collapsed.append(ch)
        pattern = "".join(collapsed)

    n_pat = len(pattern)
    n_txt = len(text)

    prev = [False] * (n_txt + 1)
    prev[0] = True

    for i in range(1, n_pat + 1):
        pc = pattern[i - 1]
        curr = [False] * (n_txt + 1)
        curr[0] = prev[0] and pc == "*"
        if pc == "*":
            for j in range(1, n_txt + 1):
                curr[j] = prev[j] or curr[j - 1]
        elif pc == "?":
            for j in range(1, n_txt + 1):
                curr[j] = prev[j - 1]
        else:
            for j in range(1, n_txt + 1):
                curr[j] = prev[j - 1] and text[j - 1] == pc
        prev = curr

    return prev[n_txt]
