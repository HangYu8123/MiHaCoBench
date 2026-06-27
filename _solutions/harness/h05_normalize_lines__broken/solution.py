"""BROKEN reference for harness/h05_normalize_lines.

PLANTED DEFECT (localized to rule 5 — width truncation): every code point is
counted as **width 1**, ignoring East-Asian wide/fullwidth characters
(``east_asian_width``) and zero-width combining marks (``combining``), and with
no grapheme-cluster protection. Rules 1–4 (line splitting, tab expansion,
internal-space collapse, NFC) are implemented correctly.

Consequences:
  * a CJK wide-character line is truncated too late (each wide char is counted
    as 1 column instead of 2), keeping more characters than ``width`` columns,
  * a base character carrying combining marks may be dropped while its marks are
    counted as a full column, and a base may be split from its marks.

Lines made only of narrow, non-combining characters are unaffected, so the
narrow tests, the tab/collapse/split tests, the NFC-composes test, and all
exception paths still pass.
"""
from __future__ import annotations

import unicodedata


def _split_lines(text: str) -> list[str]:
    """Split ``text`` on ``\\r\\n`` / lone ``\\n`` / lone ``\\r`` (rule 1)."""
    lines: list[str] = []
    cur: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\r":
            lines.append("".join(cur))
            cur = []
            if i + 1 < n and text[i + 1] == "\n":
                i += 2
            else:
                i += 1
        elif ch == "\n":
            lines.append("".join(cur))
            cur = []
            i += 1
        else:
            cur.append(ch)
            i += 1
    if cur:
        lines.append("".join(cur))
    return lines


def _expand_tabs(line: str, tabstop: int) -> str:
    """Expand each ``\\t`` to the next multiple of ``tabstop`` (rule 2)."""
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


def _collapse_internal_spaces(line: str) -> str:
    """Collapse non-leading runs of 2+ ASCII spaces to one (rule 3, no trailing strip)."""
    n_lead = len(line) - len(line.lstrip(" "))
    lead = line[:n_lead]
    rest = line[n_lead:]

    collapsed: list[str] = []
    run = 0
    for ch in rest:
        if ch == " ":
            run += 1
        else:
            if run:
                collapsed.append(" ")
                run = 0
            collapsed.append(ch)
    if run:
        collapsed.append(" ")
    return lead + "".join(collapsed)


def _truncate(line: str, width: int) -> str:
    """Truncate ``line`` to ``width`` characters.

    BUG: counts every code point as one column (ignores east_asian_width and
    combining) and offers no grapheme-cluster protection.
    """
    out: list[str] = []
    col = 0
    for ch in line:
        if col + 1 > width:
            break
        out.append(ch)
        col += 1
    return "".join(out)


def normalize(text: str, *, width: int, tabstop: int = 4) -> list[str]:
    """Display-normalize ``text`` into a list of fixed-width-ready lines.

    See TASK.md for the full rule set.

    Raises
    ------
    ValueError
        If ``width < 1`` or ``tabstop < 1``.
    """
    if width < 1:
        raise ValueError(f"width must be >= 1, got {width}")
    if tabstop < 1:
        raise ValueError(f"tabstop must be >= 1, got {tabstop}")

    result: list[str] = []
    for raw_line in _split_lines(text):
        line = _collapse_internal_spaces(raw_line)
        line = _expand_tabs(line, tabstop)
        line = line.rstrip(" ")
        line = unicodedata.normalize("NFC", line)
        line = _truncate(line, width)
        result.append(line)
    return result
