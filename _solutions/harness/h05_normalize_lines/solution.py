"""Gold reference for harness/h05_normalize_lines.

Display-normalize raw text into a list of lines fit for a fixed-width terminal,
applying a fixed pile of rules in an exact order, per logical line:

  1. line splitting on ``\\r\\n`` / lone ``\\n`` / lone ``\\r`` (no trailing
     empty line from a terminal separator; interior empty lines preserved),
  3a. collapse non-leading runs of 2+ input spaces to a single space (leading
     indentation preserved; only U+0020),
  2. true-tabstop tab expansion against the collapsed line (columns from col 0;
     one column per char here),
  3b. strip trailing spaces (including any trailing tab-fill),
  4. Unicode NFC normalisation,
  5. Unicode-aware width truncation that respects East-Asian wide chars,
     zero-width combining marks, and never splits a grapheme cluster.

Input-space collapse runs *before* tab expansion so the tab-fill spaces stay
intact (a true tabstop is observable in the output) while the collapse can shift
the column at which a later tab lands. Standard library only (``unicodedata``).
"""
from __future__ import annotations

import unicodedata


def _split_lines(text: str) -> list[str]:
    """Split ``text`` on ``\\r\\n`` / lone ``\\n`` / lone ``\\r`` (rule 1).

    A separator at the very end of ``text`` does not yield a trailing empty
    line, but an empty line between two separators is preserved.
    """
    lines: list[str] = []
    cur: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\r":
            lines.append("".join(cur))
            cur = []
            # consume a paired "\r\n" as a single separator
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
    # The leftover buffer is a final line only if it is non-empty OR the text was
    # empty; a separator at the very end must NOT add a trailing empty line.
    if cur:
        lines.append("".join(cur))
    return lines


def _expand_tabs(line: str, tabstop: int) -> str:
    """Expand each ``\\t`` to the next multiple of ``tabstop`` (rule 2).

    Columns are counted from column 0 of the line; at this stage every character
    counts as exactly one column for the purpose of locating tab stops.
    """
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
    """Collapse non-leading runs of 2+ ASCII spaces to one (rule 3).

    The leading-space (indentation) prefix is preserved exactly. A non-leading
    run of two-or-more U+0020 spaces becomes a single space; a single internal
    space is left as-is. Trailing-space stripping is *not* done here — it happens
    once, after tab expansion (so any trailing tab-fill is also removed). Only
    U+0020 is affected.
    """
    # Split off the leading-space prefix, which is preserved verbatim.
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
                collapsed.append(" ")  # any run of >=1 internal spaces -> single space
                run = 0
            collapsed.append(ch)
    if run:  # a trailing run within `rest` collapses to a single space (stripped later)
        collapsed.append(" ")
    return lead + "".join(collapsed)


def _char_width(ch: str) -> int:
    """Display column width of a single character (rule 5)."""
    if unicodedata.combining(ch) != 0:
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def _truncate(line: str, width: int) -> str:
    """Truncate ``line`` to at most ``width`` display columns (rule 5).

    Never splits a grapheme cluster (a base character plus the run of combining
    marks that immediately follow it): if admitting the next base would exceed
    ``width`` we stop before it, omitting its trailing combining marks too.
    """
    out: list[str] = []
    col = 0
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if unicodedata.combining(ch) != 0:
            # A combining mark with no admitted base (degenerate leading mark):
            # width 0, so it cannot exceed the budget — keep it and move on.
            out.append(ch)
            i += 1
            continue
        w = _char_width(ch)
        if col + w > width:
            break  # admitting this base would exceed width -> stop before it
        out.append(ch)
        col += w
        i += 1
        # Attach the run of combining marks belonging to this base (all width 0).
        while i < n and unicodedata.combining(line[i]) != 0:
            out.append(line[i])
            i += 1
    return "".join(out)


def normalize(text: str, *, width: int, tabstop: int = 4) -> list[str]:
    """Display-normalize ``text`` into a list of fixed-width-ready lines.

    Applies, per logical line and in this exact order: line splitting, true-
    tabstop tab expansion, internal-space collapse, Unicode NFC, and Unicode-
    aware width truncation. See the module docstring / TASK.md for the full
    rule set.

    Parameters
    ----------
    text : str
        Raw text to normalise.
    width : int
        Maximum display columns per line (must be >= 1).
    tabstop : int
        Tab width in columns (must be >= 1); defaults to 4.

    Returns
    -------
    list[str]
        One normalised string per logical line.

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
        # Per-line pipeline, in TASK.md's exact step order (line splitting is
        # step 1, done by _split_lines above):
        #   step 2: collapse non-leading runs of input spaces to a single space,
        #   step 3: expand tabs against the collapsed line (true tabstop from col 0),
        #   step 4: strip trailing spaces (incl. any trailing tab-fill),
        #   step 5: Unicode NFC,
        #   step 6: Unicode-aware width truncation.
        line = _collapse_internal_spaces(raw_line)
        line = _expand_tabs(line, tabstop)
        line = line.rstrip(" ")
        line = unicodedata.normalize("NFC", line)
        line = _truncate(line, width)
        result.append(line)
    return result
