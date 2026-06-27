import unicodedata


def normalize(text: str, *, width: int, tabstop: int = 4) -> list[str]:
    if width < 1:
        raise ValueError("width must be >= 1")
    if tabstop < 1:
        raise ValueError("tabstop must be >= 1")

    lines = _split_lines(text)
    return [_normalize_line(line, width, tabstop) for line in lines]


def _split_lines(text: str) -> list[str]:
    """Split on \\r\\n, lone \\n, or lone \\r."""
    lines: list[str] = []
    current: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\r":
            lines.append("".join(current))
            current = []
            if i + 1 < n and text[i + 1] == "\n":
                i += 2
            else:
                i += 1
        elif ch == "\n":
            lines.append("".join(current))
            current = []
            i += 1
        else:
            current.append(ch)
            i += 1
    if current:
        lines.append("".join(current))
    return lines


def _collapse_internal_spaces(line: str) -> str:
    """Collapse runs of 2+ ASCII spaces that are not at the start of the line."""
    idx = 0
    n = len(line)
    while idx < n and line[idx] == " ":
        idx += 1
    prefix = line[:idx]
    rest = line[idx:]

    out: list[str] = []
    space_run = 0
    for ch in rest:
        if ch == " ":
            space_run += 1
        else:
            if space_run > 0:
                out.append(" ")
                space_run = 0
            out.append(ch)
    if space_run > 0:
        out.append(" ")
    return prefix + "".join(out)


def _expand_tabs(line: str, tabstop: int) -> str:
    """Expand tabs to the next true tabstop, counting every char as one column."""
    out: list[str] = []
    col = 0
    for ch in line:
        if ch == "\t":
            spaces = tabstop - (col % tabstop)
            out.append(" " * spaces)
            col += spaces
        else:
            out.append(ch)
            col += 1
    return "".join(out)


def _char_width(ch: str) -> int:
    if unicodedata.combining(ch) != 0:
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def _truncate(line: str, width: int) -> str:
    """Truncate to at most `width` display columns without splitting graphemes."""
    out: list[str] = []
    col = 0
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if unicodedata.combining(ch) != 0:
            out.append(ch)
            i += 1
            continue
        cluster = [ch]
        w = _char_width(ch)
        j = i + 1
        while j < n and unicodedata.combining(line[j]) != 0:
            cluster.append(line[j])
            j += 1
        if col + w > width:
            break
        out.extend(cluster)
        col += w
        i = j
    return "".join(out)


def _normalize_line(line: str, width: int, tabstop: int) -> str:
    line = _collapse_internal_spaces(line)
    line = _expand_tabs(line, tabstop)
    line = line.rstrip(" ")
    line = unicodedata.normalize("NFC", line)
    line = _truncate(line, width)
    return line
