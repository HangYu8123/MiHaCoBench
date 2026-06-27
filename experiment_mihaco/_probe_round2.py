#!/usr/bin/env python3
"""Round-2 difficulty probe: do these candidate problems make naive Opus FAIL?

For each candidate we have (1) a trusted GOLD (written here), (2) an INDEPENDENT
brute oracle, (3) a fuzzer. We load the naive candidate solution from
cand_naive/probe/<id>/solution.py and differential-test it vs the gold.
Gold is first validated against the oracle, so a naive!=gold divergence is a
naive bug. Probe BEFORE investing in a full task package.

Run: python3 experiment_mihaco/_probe_round2.py [N]
"""
from __future__ import annotations
import importlib.util
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
PROBE = BENCH / "experiment_mihaco" / "cand_naive" / "probe"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def call(fn, *a, **k):
    try:
        return ("ok", fn(*a, **k))
    except Exception as e:  # noqa: BLE001
        return ("exc", type(e).__name__)


# =========================================================================== #
# TA — c_eval: integer expression with C-style (truncate-toward-zero) / and %
#   trap: Python // floors and % takes sign of divisor; spec wants trunc-to-0.
# =========================================================================== #
def ta_gold(expr: str) -> int:
    toks = _ta_tok(expr)
    val, pos = _ta_expr(toks, 0)
    if pos != len(toks):
        raise ValueError("trailing")
    return val


def _ta_tok(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1; continue
        if c.isdigit():
            j = i
            while j < n and s[j].isdigit():
                j += 1
            out.append(("num", int(s[i:j]))); i = j; continue
        if c in "+-*/%()":
            out.append((c, c)); i += 1; continue
        raise ValueError("bad char")
    return out


def _ta_expr(t, p):
    v, p = _ta_term(t, p)
    while p < len(t) and t[p][0] in "+-":
        op = t[p][0]; r, p = _ta_term(t, p + 1)
        v = v + r if op == "+" else v - r
    return v, p


def _cdiv(a, b):
    if b == 0:
        raise ZeroDivisionError
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def _cmod(a, b):
    if b == 0:
        raise ZeroDivisionError
    return a - _cdiv(a, b) * b


def _ta_term(t, p):
    v, p = _ta_unary(t, p)
    while p < len(t) and t[p][0] in "*/%":
        op = t[p][0]; r, p = _ta_unary(t, p + 1)
        v = v * r if op == "*" else (_cdiv(v, r) if op == "/" else _cmod(v, r))
    return v, p


def _ta_unary(t, p):
    if p < len(t) and t[p][0] == "-":
        v, p = _ta_unary(t, p + 1); return -v, p
    if p < len(t) and t[p][0] == "+":
        return _ta_unary(t, p + 1)
    return _ta_atom(t, p)


def _ta_atom(t, p):
    if p >= len(t):
        raise ValueError("eof")
    if t[p][0] == "num":
        return t[p][1], p + 1
    if t[p][0] == "(":
        v, p = _ta_expr(t, p + 1)
        if p >= len(t) or t[p][0] != ")":
            raise ValueError("paren")
        return v, p + 1
    raise ValueError("atom")


def ta_oracle(expr: str) -> int:
    # independent: same parse but division via math.trunc(Fraction)
    import ast
    node = ast.parse(expr, mode="eval").body

    def ev(n):
        if isinstance(n, ast.Constant):
            return int(n.value)
        if isinstance(n, ast.UnaryOp):
            x = ev(n.operand)
            return -x if isinstance(n.op, ast.USub) else +x
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add): return a + b
            if isinstance(n.op, ast.Sub): return a - b
            if isinstance(n.op, ast.Mult): return a * b
            if isinstance(n.op, ast.Div):
                if b == 0: raise ZeroDivisionError
                return math.trunc(Fraction(a, b))
            if isinstance(n.op, ast.Mod):
                if b == 0: raise ZeroDivisionError
                return a - math.trunc(Fraction(a, b)) * b
        raise ValueError("unsupported")
    return ev(node)


def _ta_gen(rng, depth):
    if depth <= 0 or rng.random() < 0.4:
        v = rng.randint(-9, 9)
        return f"({v})" if v < 0 else str(v)
    op = rng.choice(["+", "-", "*", "/", "%"])
    return "(" + _ta_gen(rng, depth - 1) + op + _ta_gen(rng, depth - 1) + ")"


def probe_ta(rng):
    gpath = PROBE / "ta_c_eval" / "solution.py"
    if not gpath.exists():
        print("TA: no naive solution yet"); return None
    naive = load(gpath, "ta_naive").evaluate
    # validate gold vs oracle
    bad = 0
    for _ in range(N):
        e = _ta_gen(rng, rng.randint(1, 4))
        g, o = call(ta_gold, e), call(ta_oracle, e)
        if g != o and not (g[0] == o[0] == "exc"):
            bad += 1
    div, ex = 0, []
    for _ in range(N):
        e = _ta_gen(rng, rng.randint(1, 4))
        g, v = call(ta_gold, e), call(naive, e)
        ok = (g[0] == v[0] == "exc") or (g == v)
        if not ok:
            div += 1
            if len(ex) < 6: ex.append((e, g, v))
    print(f"\n=== TA c_eval: gold-vs-oracle mismatches={bad}; naive diverged {div}/{N} ===")
    for e, g, v in ex:
        print(f"   {e!r}  gold={g}  naive={v}")
    return div


# =========================================================================== #
# TB — envelopes: longest chain where (w1<w2 and h1<h2) strictly.
#   trap: sort by (w asc, h asc) then LIS on h overcounts equal-w; correct is
#   (w asc, h DESC) then strictly-increasing LIS on h.
# =========================================================================== #
def tb_gold(boxes):
    if not boxes:
        return 0
    bs = sorted(boxes, key=lambda p: (p[0], -p[1]))
    tails = []
    import bisect
    for _, h in bs:
        i = bisect.bisect_left(tails, h)
        if i == len(tails):
            tails.append(h)
        else:
            tails[i] = h
    return len(tails)


def tb_oracle(boxes):
    # independent brute: longest path in the strict-dominance DAG, O(n^2) DP
    n = len(boxes)
    if n == 0:
        return 0
    order = sorted(range(n), key=lambda i: (boxes[i][0] + boxes[i][1]))
    best = [1] * n
    res = 1
    for a in range(n):
        i = order[a]
        for b in range(a):
            j = order[b]
            if boxes[j][0] < boxes[i][0] and boxes[j][1] < boxes[i][1]:
                if best[j] + 1 > best[i]:
                    best[i] = best[j] + 1
        res = max(res, best[i])
    return res


def probe_tb(rng):
    gpath = PROBE / "tb_envelopes" / "solution.py"
    if not gpath.exists():
        print("TB: no naive solution yet"); return None
    naive = load(gpath, "tb_naive").max_nested
    bad, div, ex = 0, 0, []
    for _ in range(N):
        n = rng.randint(0, 8)
        boxes = [(rng.randint(1, 5), rng.randint(1, 5)) for _ in range(n)]  # small range => many ties
        g, o = call(tb_gold, list(boxes)), call(tb_oracle, list(boxes))
        if g != o:
            bad += 1
        v = call(naive, list(boxes))
        if g != v:
            div += 1
            if len(ex) < 6: ex.append((boxes, g, v))
    print(f"\n=== TB envelopes: gold-vs-oracle mismatches={bad}; naive diverged {div}/{N} ===")
    for b, g, v in ex:
        print(f"   {b}  gold={g}  naive={v}")
    return div


# =========================================================================== #
# TC — wildcard match: '?'=one char, '*'=any run (incl empty); full match.
# =========================================================================== #
def tc_gold(p, s):
    np_, ns = len(p), len(s)
    dp = [[False] * (ns + 1) for _ in range(np_ + 1)]
    dp[0][0] = True
    for i in range(1, np_ + 1):
        if p[i - 1] == "*":
            dp[i][0] = dp[i - 1][0]
    for i in range(1, np_ + 1):
        for j in range(1, ns + 1):
            if p[i - 1] == "*":
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif p[i - 1] == "?" or p[i - 1] == s[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
    return dp[np_][ns]


def tc_oracle(p, s):
    from functools import lru_cache

    @lru_cache(None)
    def go(i, j):
        if i == len(p):
            return j == len(s)
        if p[i] == "*":
            return go(i + 1, j) or (j < len(s) and go(i, j + 1))
        if j < len(s) and (p[i] == "?" or p[i] == s[j]):
            return go(i + 1, j + 1)
        return False
    return go(0, 0)


def probe_tc(rng):
    gpath = PROBE / "tc_wildcard" / "solution.py"
    if not gpath.exists():
        print("TC: no naive solution yet"); return None
    naive = load(gpath, "tc_naive").is_match
    bad, div, ex = 0, 0, []
    alpha = "ab"
    for _ in range(N):
        s = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 7)))
        p = "".join(rng.choice(alpha + "?*") for _ in range(rng.randint(0, 7)))
        g, o = call(tc_gold, p, s), call(tc_oracle, p, s)
        if g != o:
            bad += 1
        v = call(naive, p, s)
        if g != v:
            div += 1
            if len(ex) < 6: ex.append((p, s, g, v))
    print(f"\n=== TC wildcard: gold-vs-oracle mismatches={bad}; naive diverged {div}/{N} ===")
    for p, s, g, v in ex:
        print(f"   p={p!r} s={s!r}  gold={g}  naive={v}")
    return div


if __name__ == "__main__":
    print(f"Round-2 probe, N={N}")
    res = {}
    for name, fn in [("TA", probe_ta), ("TB", probe_tb), ("TC", probe_tc)]:
        rng = random.Random(20260618)
        res[name] = fn(rng)
    print("\n==== SUMMARY ====")
    for k, v in res.items():
        if v is None:
            tag = "no naive yet"
        elif v > 0:
            tag = "NAIVE FAILS (discriminating candidate)"
        else:
            tag = "naive-solved"
        print(f"  {k}: {v} -> {tag}")
