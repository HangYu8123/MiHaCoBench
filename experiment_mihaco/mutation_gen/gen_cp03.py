"""Generate the oracle-grounded mutation corpus for competitive/cp03_string_period.

Independent oracle: Python's stdlib ``re`` engine (a TRUE external implementation,
not authored here). Wildcard '?' -> '.', literals escaped, ``re.DOTALL`` so '?'
matches every character including newline, ``Pattern.fullmatch(text, i, i+m)`` per
window so there is no '^' anchor gotcha. Empty / too-long patterns return [].

Provenance: wildcard pattern matching — cf. LeetCode 44 (Wildcard Matching; note
it also allows '*'); the '?'-only sliding-window form is linear (Wikipedia
"Matching wildcards"; cp-algorithms Z-function). The corpus cross-validates the
gold Z-algorithm against ``re`` and keeps inputs that kill correctness mutants.

Run:  python3 experiment_mihaco/mutation_gen/gen_cp03.py
"""
from __future__ import annotations

import re
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

from _lib import grading_utils as gu  # noqa: E402
import _mutation_seed as ms  # noqa: E402

CATEGORY, TASK_ID = "competitive", "cp03_string_period"
GOLD_DIR = gu.GOLD_ROOT / CATEGORY / TASK_ID
GOLD_SRC = (GOLD_DIR / "solution.py").read_text()
gold = ms.load_callable_from_source(GOLD_SRC, "count_pattern")


# --- Independent external oracle: Python re --------------------------------- #
def oracle(text: str, pattern: str) -> list[int]:
    if pattern == "" or len(pattern) > len(text):
        return []
    rx = re.compile("".join("." if ch == "?" else re.escape(ch) for ch in pattern), re.DOTALL)
    m = len(pattern)
    return [i for i in range(len(text) - m + 1) if rx.fullmatch(text, i, i + m)]


# --- Hand-written "common-mistake" wrong solutions ------------------------- #
_WRONG_SOURCES = {
    "one_indexed": '''
def count_pattern(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0 or m > n: return []
    out = []
    for i in range(n - m + 1):
        if all(p == '?' or p == t for p, t in zip(pattern, text[i:i+m])):
            out.append(i + 1)   # BUG: 1-indexed
    return out
''',
    "miss_last": '''
def count_pattern(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0 or m > n: return []
    out = []
    for i in range(n - m):       # BUG: off-by-one, misses the last position
        if all(p == '?' or p == t for p, t in zip(pattern, text[i:i+m])):
            out.append(i)
    return out
''',
    "wildcard_literal": '''
def count_pattern(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0 or m > n: return []
    out = []
    for i in range(n - m + 1):
        if pattern == text[i:i+m]:   # BUG: treats '?' as a literal char
            out.append(i)
    return out
''',
    "first_only": '''
def count_pattern(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0 or m > n: return []
    for i in range(n - m + 1):
        if all(p == '?' or p == t for p, t in zip(pattern, text[i:i+m])):
            return [i]              # BUG: returns only the first match
    return []
''',
    "empty_pattern_all": '''
def count_pattern(text, pattern):
    n, m = len(text), len(pattern)
    if m > n: return []
    out = []                        # BUG: empty pattern matches everywhere
    for i in range(n - m + 1):
        if all(p == '?' or p == t for p, t in zip(pattern, text[i:i+m])):
            out.append(i)
    return out
''',
}


def _wrong_fns():
    wrongs = [(name, ms.load_callable_from_source(src, "count_pattern"))
              for name, src in _WRONG_SOURCES.items()]
    for label, src in ms.generate_mutants(GOLD_SRC):
        try:
            wrongs.append((label, ms.load_callable_from_source(src, "count_pattern")))
        except Exception:
            continue
    return wrongs


def _inputs():
    rng = random.Random(20260616)
    out = []
    alphabets = ["ab", "abc", "ab#.", "a*?b"]   # include regex-special chars as LITERAL text/pattern
    for _ in range(4000):
        alpha = rng.choice(alphabets)
        n = rng.randint(0, 28)
        text = "".join(rng.choice(alpha) for _ in range(n))
        m = rng.randint(0, min(6, max(1, n)))
        pat_chars = [rng.choice(alpha + "?") for _ in range(m)]
        pattern = "".join(pat_chars)
        out.append((text, pattern))
    # explicit edge cases
    out += [("", ""), ("", "a"), ("a", ""), ("a", "a"), ("a", "b"), ("a", "?"),
            ("aaaa", "aa"), ("aaaa", "a?"), ("a\nb", "a?b"), ("a#b#a#b", "a#b"),
            ("a.b", "a.b"), ("a.b", "a?b"), ("xxx", "????")]
    return out


def main() -> int:
    wrongs = _wrong_fns()
    corpus = ms.build_corpus(gold, oracle, wrongs, _inputs(), max_keep=150)
    out = ms.write_corpus(ROOT / "tasks" / CATEGORY / TASK_ID, corpus, meta_extra={
        "oracle": "python stdlib re (DOTALL, fullmatch-per-window) — true external engine",
        "provenance": "LeetCode 44 (wildcard); '?'-only linear matching (Wikipedia Matching wildcards / cp-algorithms Z-function)",
        "input_seed": 20260616,
    })
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
