#!/usr/bin/env python3
"""Differential fuzz naive regex vs re.fullmatch (oracle), backtracking-safe.

Each re/naive call runs under a SIGALRM guard; pathological patterns (where re
catastrophically backtracks) are skipped as not-oracle-usable. Reports
correctness divergences on the oracle-valid cases.
"""
import importlib.util
import random
import re
import signal
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
SOL = BENCH / "experiment_mihaco" / "cand_naive" / "probe" / "td_regex" / "solution.py"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000

spec = importlib.util.spec_from_file_location("rgx", SOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
naive = mod.fullmatch

ALPHA = "abc"


class _TO(Exception):
    pass


def _guard(seconds, fn, *a):
    def h(signum, frame):
        raise _TO()
    old = signal.signal(signal.SIGALRM, h)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return ("ok", fn(*a))
    except _TO:
        return ("timeout", None)
    except re.error:
        return ("re_error", None)
    except Exception as e:  # noqa: BLE001
        return ("exc", type(e).__name__)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def gen_atom(rng, depth):
    r = rng.random()
    if depth > 0 and r < 0.16:
        return "(" + gen_alt(rng, depth - 1) + ")"
    if r < 0.30:
        return "."
    if r < 0.45:
        neg = rng.random() < 0.4
        body = ""
        for _ in range(rng.randint(1, 3)):
            if rng.random() < 0.4:
                lo = rng.choice("ac")
                hi = {"a": "c", "c": "e"}[lo]
                body += f"{lo}-{hi}"
            else:
                body += rng.choice(ALPHA)
        return "[" + ("^" if neg else "") + body + "]"
    if r < 0.55:
        return "\\" + rng.choice(".*+?()[]|\\")
    return rng.choice(ALPHA)


def gen_quant(rng, depth):
    a = gen_atom(rng, depth)
    q = rng.random()
    if q < 0.25:
        return a + "*"
    if q < 0.45:
        return a + "+"
    if q < 0.60:
        return a + "?"
    return a


def gen_seq(rng, depth):
    return "".join(gen_quant(rng, depth) for _ in range(rng.randint(0, 4)))


def gen_alt(rng, depth):
    parts = [gen_seq(rng, depth) for _ in range(rng.randint(1, 3))]
    return "|".join(parts)


def main():
    rng = random.Random(20260618)
    div = 0
    tested = 0
    skipped = 0
    examples = []
    for _ in range(N):
        p = gen_alt(rng, rng.randint(1, 3))
        t = "".join(rng.choice("abcde") for _ in range(rng.randint(0, 7)))
        ro = _guard(0.4, lambda: re.fullmatch(p, t) is not None)
        if ro[0] != "ok":
            skipped += 1
            continue
        tested += 1
        nv = _guard(0.4, lambda: bool(naive(p, t)))
        if nv[0] != "ok" or nv[1] != ro[1]:
            div += 1
            if len(examples) < 20:
                examples.append((p, t, ro[1], nv))
    pct = 100.0 * div / tested if tested else 0.0
    print(f"regex naive vs re.fullmatch: {div}/{tested} diverged ({pct:.2f}%); "
          f"{skipped} skipped (re pathological)")
    for p, t, r, nv in examples:
        print(f"   p={p!r:22} t={t!r:12} re={r}  naive={nv}")


if __name__ == "__main__":
    main()
