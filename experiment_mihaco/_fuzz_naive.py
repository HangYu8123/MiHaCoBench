#!/usr/bin/env python3
"""Differential fuzz: naive candidate vs gold reference, per harness task.

For each task, generate many deterministic random inputs, call BOTH the gold
(_solutions) and the naive (cand_naive) implementation, and report any input
where they diverge (different return value, or different exception behaviour).
Gold is self-checked against an independent oracle, so a divergence is a latent
naive bug -> a candidate hardened/discriminating test case.

Run: python3 experiment_mihaco/_fuzz_naive.py [N]
"""
from __future__ import annotations
import importlib.util
import random
import sys
import traceback
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
GOLD = BENCH / "_solutions" / "harness"
NAIVE = BENCH / "experiment_mihaco" / "cand_naive" / "harness"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def call(fn, *a, **k):
    """Return ('ok', value) or ('exc', ExcTypeName)."""
    try:
        return ("ok", fn(*a, **k))
    except Exception as e:  # noqa: BLE001
        return ("exc", type(e).__name__)


def cmp_result(g, nv):
    return g == nv


def report(task, diverged, total, examples):
    pct = 100.0 * diverged / total if total else 0.0
    print(f"\n=== {task}: {diverged}/{total} diverged ({pct:.1f}%) ===")
    for i, ex in enumerate(examples[:8]):
        print(f"  [{i}] input={ex['in']!r}\n      gold ={ex['gold']!r}\n      naive={ex['naive']!r}")


# --------------------------------------------------------------------------- #
def fuzz_h01(rng):
    gold = load(GOLD / "h01_apportion_seats" / "solution.py", "g01").apportion
    nv = load(NAIVE / "h01_apportion_seats" / "solution.py", "n01").apportion
    div, ex = 0, []
    for _ in range(N):
        n = rng.randint(0, 6)
        # bias toward ties & zeros
        votes = [rng.choice([0, 1, 1, 2, 2, 3, 5, rng.randint(0, 9)]) for _ in range(n)]
        seats = rng.randint(0, 15)
        g = call(gold, list(votes), seats)
        v = call(nv, list(votes), seats)
        if g != v:
            div += 1
            if len(ex) < 8:
                ex.append({"in": (votes, seats), "gold": g, "naive": v})
    report("h01_apportion_seats", div, N, ex)
    return div


def fuzz_h02(rng):
    gold = load(GOLD / "h02_merge_intervals" / "solution.py", "g02").merge
    nv = load(NAIVE / "h02_merge_intervals" / "solution.py", "n02").merge
    div, ex = 0, []
    for _ in range(N):
        k = rng.randint(0, 7)
        ivs = []
        for _ in range(k):
            a = rng.randint(-4, 8)
            b = a + rng.choice([0, 0, 1, 1, 2, 3])  # many adjacent/zero-length
            ivs.append((a, b))
        g = call(gold, list(ivs))
        v = call(nv, list(ivs))
        if g != v:
            div += 1
            if len(ex) < 8:
                ex.append({"in": ivs, "gold": g, "naive": v})
    report("h02_merge_intervals", div, N, ex)
    return div


def fuzz_h03(rng):
    GB = load(GOLD / "h03_token_bucket" / "solution.py", "g03").TokenBucket
    NB = load(NAIVE / "h03_token_bucket" / "solution.py", "n03").TokenBucket
    div, ex = 0, []
    for _ in range(N):
        cap = rng.choice([1, 2, 5, 10])
        rate = rng.choice([0, 1, 2, 3])
        calls = []
        t = 0
        for _ in range(rng.randint(1, 10)):
            t += rng.choice([0, 0, 1, 2, 3, 5])
            cost = rng.choice([1, 2, 3, 5, cap])
            calls.append((t, cost))
        gb, nb = GB(cap, rate), NB(cap, rate)
        gseq = [call(gb.allow, t, c) for (t, c) in calls]
        nseq = [call(nb.allow, t, c) for (t, c) in calls]
        if gseq != nseq:
            div += 1
            if len(ex) < 8:
                ex.append({"in": (cap, rate, calls), "gold": gseq, "naive": nseq})
    report("h03_token_bucket", div, N, ex)
    return div


_NUMS = ["0", "1", "2", "3", "4", "5", "2.5", ".5", "10"]
_BIN = ["+", "-", "*", "/", "**"]


def _gen_expr(rng, depth):
    if depth <= 0 or rng.random() < 0.3:
        atom = rng.choice(_NUMS)
        if rng.random() < 0.3:
            atom = ("-" * rng.randint(1, 2)) + atom  # unary
        return atom
    if rng.random() < 0.25:
        return "(" + _gen_expr(rng, depth - 1) + ")"
    if rng.random() < 0.25:
        return "-" + _gen_expr(rng, depth - 1)
    return _gen_expr(rng, depth - 1) + rng.choice(_BIN) + _gen_expr(rng, depth - 1)


def fuzz_h04(rng):
    gold = load(GOLD / "h04_expr_eval" / "solution.py", "g04").evaluate
    nv = load(NAIVE / "h04_expr_eval" / "solution.py", "n04").evaluate
    div, ex = 0, []
    for _ in range(N):
        e = _gen_expr(rng, rng.randint(1, 4))
        g = call(gold, e)
        v = call(nv, e)
        ok = (g[0] == v[0] == "exc" and g[1] == v[1]) or (
            g[0] == v[0] == "ok"
            and (abs(g[1] - v[1]) <= 1e-9 + 1e-6 * abs(g[1]) if isinstance(g[1], float) else g[1] == v[1])
        )
        if not ok:
            div += 1
            if len(ex) < 8:
                ex.append({"in": e, "gold": g, "naive": v})
    report("h04_expr_eval", div, N, ex)
    return div


_CHARS = ["a", "b", " ", " ", "\t", "\r", "\n", "漢", "字",
          "ｗ", "́", "̂", "x", "é", "れ", "z"]


def fuzz_h05(rng):
    gold = load(GOLD / "h05_normalize_lines" / "solution.py", "g05").normalize
    nv = load(NAIVE / "h05_normalize_lines" / "solution.py", "n05").normalize
    div, ex = 0, []
    for _ in range(N):
        s = "".join(rng.choice(_CHARS) for _ in range(rng.randint(0, 14)))
        w = rng.randint(1, 10)
        ts = rng.randint(1, 6)
        g = call(gold, s, width=w, tabstop=ts)
        v = call(nv, s, width=w, tabstop=ts)
        if g != v:
            div += 1
            if len(ex) < 8:
                ex.append({"in": (s, w, ts), "gold": g, "naive": v})
    report("h05_normalize_lines", div, N, ex)
    return div


def _gen_ops(rng):
    accts = ["A", "B", "C", "D"]
    types = ["deposit", "withdraw", "transfer", "hold", "release", "fee"]
    ops = []
    nid = 1
    nseq = 1
    # seed some deposits
    for _ in range(rng.randint(2, 4)):
        a = rng.choice(accts)
        ops.append({"id": nid, "seq": nseq, "ts": rng.randint(0, 3), "type": "deposit",
                    "group": None, "acct": a, "amt": rng.randint(10, 200)})
        nid += 1
        nseq += 1
    for _ in range(rng.randint(2, 10)):
        t = rng.choice(types)
        ts = rng.randint(0, 6)
        grp = rng.choice([None, None, 1, 2])
        op = {"id": nid, "seq": nseq, "ts": ts, "type": t, "group": grp, "amt": rng.randint(1, 120)}
        if t == "transfer":
            op["src"] = rng.choice(accts)
            op["dst"] = rng.choice(accts)
        else:
            op["acct"] = rng.choice(accts)
        ops.append(op)
        nid += 1
        nseq += 1
    rng.shuffle(ops)
    return ops


def fuzz_h06(rng):
    gold = load(GOLD / "h06_replay_ledger" / "solution.py", "g06").replay
    nv = load(NAIVE / "h06_replay_ledger" / "solution.py", "n06").replay
    div, ex = 0, []
    for _ in range(N):
        ops = _gen_ops(rng)
        g = call(gold, [dict(o) for o in ops])
        v = call(nv, [dict(o) for o in ops])
        if g != v:
            div += 1
            if len(ex) < 8:
                ex.append({"in": ops, "gold": g, "naive": v})
    report("h06_replay_ledger", div, N, ex)
    return div


if __name__ == "__main__":
    print(f"Differential fuzz: naive vs gold, N={N} per task")
    results = {}
    for name, fn in [("h01", fuzz_h01), ("h02", fuzz_h02), ("h03", fuzz_h03),
                     ("h04", fuzz_h04), ("h05", fuzz_h05), ("h06", fuzz_h06)]:
        rng = random.Random(20260618)  # same seed per task for reproducibility
        try:
            results[name] = fn(rng)
        except Exception:
            print(f"\n=== {name}: FUZZER ERROR ===")
            traceback.print_exc()
            results[name] = -1
    print("\n\n==== SUMMARY (divergences found) ====")
    for k, v in results.items():
        tag = "LATENT BUG (discriminating potential)" if v > 0 else ("genuinely naive-solved" if v == 0 else "fuzzer error")
        print(f"  {k}: {v}  -> {tag}")
