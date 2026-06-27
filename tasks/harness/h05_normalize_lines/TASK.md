# Harness 05 — `normalize_lines`: Display-Normalize Log Lines (Unicode-Aware)

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 6

Display-normalize raw text (e.g. log output) into a list of lines fit for a
fixed-width terminal column. The difficulty is the **pile of independent, subtle
rules** that must be applied **in an exact order**, and a width calculation that
is **Unicode-aware** (CJK double-width characters, zero-width combining marks,
and grapheme clusters that must not be split). Misreading any single rule
changes the output.

Implement your solution in a single file `solution.py`. Use **only the Python
standard library**; the only module you need beyond builtins is `unicodedata`.
No third-party packages.

## Public contract

### `normalize(text: str, *, width: int, tabstop: int = 4) -> list[str]`

Split `text` into logical lines and return each line **display-normalized**.
Per logical line, apply the steps below **in exactly this order** (note that the
space-collapse step is split around tab expansion — that ordering is part of the
contract):

1. **Line splitting.** Lines are separated by `"\r\n"`, a lone `"\n"`, **or** a
   lone `"\r"` (classic-Mac). A separator at the **very end** of `text` does
   **not** create a trailing empty line, but an empty line *between* two
   separators **is** preserved. Examples:
   * `"a\n\nb"` → `["a", "", "b"]`
   * `"a\n"` → `["a"]`
   * `"a\rb"` → `["a", "b"]`
   * `"a\r\nb"` → `["a", "b"]` (the `\r\n` is **one** separator, not two)
   * `""` → `[]`

2. **Internal-space collapse (input spaces).** Collapse every run of **2 or more
   ASCII spaces** (U+0020) that is **not at the start of the line** into a single
   space. **Leading** spaces (the indentation prefix) are preserved **exactly**.
   (Only U+0020 is affected. Trailing spaces are handled in step 4, not here.)
   This runs *before* tab expansion, so collapsing can change the column at which
   a later tab lands. Examples:
   * `"x  y   z"` → `"x y z"`
   * `"   indented  text"` → `"   indented text"` (leading 3 spaces kept)

3. **Tab expansion (true tabstop).** Expand each `"\t"` to the number of spaces
   needed to reach the **next multiple of `tabstop`**, counted in **columns from
   column 0 of the line** (a *true* tabstop — NOT a fixed number of spaces).
   Every character (including any wide character) counts as **one** column for
   the purpose of locating tab stops. The spaces a tab emits are **not**
   themselves subject to step 2's collapse. With `tabstop=4`:
   * `"a\tb"` → `"a   b"` (`a` at col 0; the tab fills cols 1–3; `b` lands at col 4)
   * `"ab\tc"` → `"ab  c"` (`ab` at cols 0–1; the tab fills cols 2–3; `c` at col 4)

4. **Strip trailing spaces.** Remove all trailing U+0020 spaces from the line
   (this includes any trailing tab-fill produced by step 3). E.g. a line that is
   only spaces becomes `""`, and `"hello world   "` becomes `"hello world"`.

5. **Unicode NFC.** Apply `unicodedata.normalize("NFC", line)` to the line.

6. **Width truncation.** Truncate the line to at most `width` **display
   columns** (measured **after** NFC). The column width of a character `ch` is:
   * `0` if `unicodedata.combining(ch) != 0` (a combining mark);
   * else `2` if `unicodedata.east_asian_width(ch) in ("W", "F")` (wide / fullwidth);
   * else `1`.

   A **grapheme cluster** here means a base character together with the run of
   combining marks that immediately follow it. You must **never split a grapheme
   cluster**: if appending the next **base** character would push the running
   column total **above** `width`, **stop before that base character** (and
   therefore also omit the trailing combining marks that belong to it). Combining
   marks (width 0) that ride on a base character that *was* admitted are always
   kept. **No ellipsis** or other marker is added.

### Exceptions

Assert exception **types**; messages are unspecified.

| Condition | Raise |
|-----------|-------|
| `width < 1` | `ValueError` |
| `tabstop < 1` | `ValueError` |

## Worked examples

```python
normalize("a\tb", width=80)                 == ["a   b"]            # step 3: tab to col 4 (fill not collapsed)
normalize("x  y   z", width=80)             == ["x y z"]           # step 2: internal runs collapse
normalize("   indented  text", width=80)    == ["   indented text"] # leading 3 spaces kept; internal run collapsed
normalize("hello world   ", width=80)       == ["hello world"]     # step 4: trailing spaces stripped
normalize("a\r\nb\rc\n", width=80)          == ["a", "b", "c"]     # step 1: \r\n, lone \r, trailing \n
```

The collapse-then-expand order is observable: `normalize("a  \tb", width=80)`
first collapses the input `"  "` to one space (`"a \tb"`), then the tab at column
2 fills to column 4, giving `["a   b"]`.

**Wide-character truncation.** Take the string `"漢字ab"`. Each of `漢` and `字`
is East-Asian *Wide* (column width 2); `a` and `b` are width 1. So the column
widths are `2, 2, 1, 1`. With `width=3`, only `漢` (2 columns) fits; adding `字`
would reach 4 > 3, so we stop:

```python
normalize("漢字ab", width=3)                 == ["漢"]
normalize("漢字ab", width=4)                 == ["漢字"]
```

**Combining-mark truncation (NFC composes).** The string `"éxy"` is
`e` + COMBINING ACUTE ACCENT + `x` + `y`. NFC composes the first two into the
single code point `é` (U+00E9, width 1), giving widths `1, 1, 1`. With `width=2`:

```python
normalize("éxy", width=2)        == ["éx"]          # i.e. ["éx"]
```

**Combining-mark truncation (stays decomposed).** The string
`"x́̂yz"` is `x` + COMBINING ACUTE ACCENT + COMBINING CIRCUMFLEX
ACCENT + `y` + `z`. `x` has **no** precomposed form with these two marks, so NFC
leaves it as `x` followed by two width-0 combining marks. The column widths are
`1, 0, 0, 1, 1`. With `width=1`, the base `x` (width 1) fits and its two
combining marks (width 0) ride along, but `y` would push the total to 2 > 1, so:

```python
normalize("x́̂yz", width=1)  == ["x́̂"]  # x + the two marks, nothing else
```

## Notes

* The steps are applied **independently per logical line** and in the **exact
  order** above: input-space collapse (step 2) happens *before* tab expansion
  (step 3); trailing-space stripping (step 4) happens *after* tab expansion; and
  NFC (step 5) happens *before* width truncation (step 6).
* The function is **pure** and **deterministic**: the output is fully determined
  by `(text, width, tabstop)`; no seeds, clock, or I/O.
* `unicodedata` is the only module you should need beyond builtins.
