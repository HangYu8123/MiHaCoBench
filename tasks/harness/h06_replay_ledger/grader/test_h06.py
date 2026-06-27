"""Grader for harness/h06_replay_ledger.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference applies an atomic group's ops to the live state immediately
and, on a rejection inside the group, records all ids as rejected but only undoes
the *failing* op's (no-op) effect — it does NOT roll back the earlier ops of the
group that already succeeded (a hold / a transfer stay applied). The
atomic-group-rollback tests and the independent oracle catch this; non-group
cases, all-success groups, and the validation paths still pass on the broken
variant.

The independent oracle (``_oracle`` below) is structurally different from any
intended solution: it deep-copies the WHOLE account state before each unit, tries
the unit op-by-op, and restores the whole copy on any failure. It does not import
the gold. The scale/time gate then proves the solution is not O(n^2) (the oracle
itself is only ever run on tiny inputs).
"""
from __future__ import annotations

import copy
import random

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h06_replay_ledger"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

replay = gu.load_callable(SOL, "solution.py", "replay")

# Hard-gate parameters — MUST match TASK.md exactly.
GATE_N = 50_000
GATE_SEED = 20260618
GATE_TIMEOUT = 6.0


# ===========================================================================
# Independent oracle (structurally different; never imports the gold).
# ===========================================================================
_OP_FIELDS = {
    "deposit": ("acct", "amt"),
    "withdraw": ("acct", "amt"),
    "transfer": ("src", "dst", "amt"),
    "hold": ("acct", "amt"),
    "release": ("acct", "amt"),
    "fee": ("acct", "amt"),
}


def _accts_of(op: dict):
    if op["type"] == "transfer":
        return (op["src"], op["dst"])
    return (op["acct"],)


def _apply(state: dict, op: dict) -> bool:
    """Apply one op to ``state`` ({acct: {'balance','held'}}). Return success."""
    t, amt = op["type"], op["amt"]
    for a in _accts_of(op):
        state.setdefault(a, {"balance": 0, "held": 0})
    if t == "deposit":
        state[op["acct"]]["balance"] += amt
        return True
    if t == "withdraw":
        s = state[op["acct"]]
        if s["balance"] - s["held"] < amt:
            return False
        s["balance"] -= amt
        return True
    if t == "transfer":
        s, d = state[op["src"]], state[op["dst"]]
        if s["balance"] - s["held"] < amt:
            return False
        s["balance"] -= amt
        d["balance"] += amt
        return True
    if t == "hold":
        s = state[op["acct"]]
        if s["balance"] - s["held"] < amt:
            return False
        s["held"] += amt
        return True
    if t == "release":
        s = state[op["acct"]]
        if s["held"] < amt:
            return False
        s["held"] -= amt
        return True
    # fee
    s = state[op["acct"]]
    if s["balance"] - s["held"] < amt:
        return False
    s["balance"] -= amt
    return True


def _oracle(ops: list[dict]) -> dict:
    """Trusted, deliberately simple reference.

    Validation mirrors the contract; processing deep-copies the whole state
    before each unit and restores it wholesale on a group rejection. Units are
    processed in ``(ts, seq)`` order keyed by their earliest member, with a group
    handled as one contiguous block. O(units * |state|) — only for tiny inputs.
    """
    # --- validation (raise ValueError, aborting) ---
    base = ("id", "seq", "ts", "type", "group")
    seen_ids, seen_seqs = set(), set()
    for op in ops:
        for f in base:
            if f not in op:
                raise ValueError("missing base field")
        if op["type"] not in _OP_FIELDS:
            raise ValueError("unknown type")
        for f in _OP_FIELDS[op["type"]]:
            if f not in op:
                raise ValueError("missing type field")
        if op["amt"] <= 0:
            raise ValueError("amt<=0")
        if op["id"] in seen_ids:
            raise ValueError("dup id")
        seen_ids.add(op["id"])
        if op["seq"] in seen_seqs:
            raise ValueError("dup seq")
        seen_seqs.add(op["seq"])

    order = sorted(ops, key=lambda o: (o["ts"], o["seq"]))

    # Build units: singletons (group None) and atomic groups keyed by (ts, group).
    # Each unit tagged with its earliest (ts, seq) for processing order.
    units = []  # (sort_key, [ops])
    group_idx: dict[tuple, int] = {}
    for op in order:
        g = op["group"]
        if g is None:
            units.append([(op["ts"], op["seq"]), [op]])
            continue
        key = (op["ts"], g)
        if key not in group_idx:
            group_idx[key] = len(units)
            units.append([(op["ts"], op["seq"]), []])
        units[group_idx[key]][1].append(op)
    units.sort(key=lambda u: u[0])

    state: dict = {}
    rejected: list[int] = []
    for _key, unit in units:
        if len(unit) == 1 and unit[0]["group"] is None:
            op = unit[0]
            for a in _accts_of(op):
                state.setdefault(a, {"balance": 0, "held": 0})
            if not _apply(state, op):
                rejected.append(op["id"])
            continue
        # Atomic group: copy whole state, try, restore on failure.
        for op in unit:
            for a in _accts_of(op):
                state.setdefault(a, {"balance": 0, "held": 0})
        backup = copy.deepcopy(state)
        ok = all(_apply(state, op) for op in unit)
        # `all` short-circuits, matching "stop at first rejection".
        if not ok:
            state = backup
            for op in unit:
                rejected.append(op["id"])

    accounts = {a: {"balance": s["balance"], "held": s["held"]} for a, s in state.items()}
    return {"accounts": accounts, "rejected": rejected}


# ===========================================================================
# Deterministic op-list builders (no committed data; fixed seeds).
# ===========================================================================
def _op(id_, seq, ts, type_, group=None, **fields):
    d = {"id": id_, "seq": seq, "ts": ts, "type": type_, "group": group}
    d.update(fields)
    return d


def _worked_example():
    return [
        _op(10, 1, 1, "deposit", None, acct="A", amt=100),
        _op(11, 2, 1, "deposit", None, acct="B", amt=50),
        _op(12, 3, 2, "hold", None, acct="A", amt=60),
        _op(13, 4, 3, "withdraw", None, acct="A", amt=50),
        _op(14, 5, 5, "hold", 1, acct="B", amt=30),
        _op(15, 6, 5, "transfer", 1, src="A", dst="C", amt=20),
        _op(16, 7, 5, "withdraw", 1, acct="B", amt=25),
    ]


def _rand_oplist(seed: int, n_ops: int, n_accts: int, p_group: float,
                 max_ts: int) -> list[dict]:
    """A deterministic, VALID pseudo-random op-list (unique id & seq, amt>0).

    Groups are formed by giving several consecutive ops (in seq order) the same
    (ts, group); the generator never creates a duplicate id/seq and always uses
    amt>0, so the only rejections come from the balance/hold semantics — exactly
    what the oracle and the solution must agree on.
    """
    rng = random.Random(seed)
    types = ["deposit", "withdraw", "transfer", "hold", "release", "fee"]
    accts = [f"acct{i}" for i in range(n_accts)]
    ops: list[dict] = []
    seq = 0
    next_group = 1
    i = 0
    while i < n_ops:
        ts = rng.randint(1, max_ts)
        # Sometimes emit a small atomic group sharing one ts/group; else a single op.
        if rng.random() < p_group and n_ops - i >= 2:
            size = rng.randint(2, 3)
            g = next_group
            next_group += 1
            for _ in range(size):
                seq += 1
                ops.append(_mk_op(rng, len(ops), seq, ts, g, types, accts))
                i += 1
        else:
            seq += 1
            ops.append(_mk_op(rng, len(ops), seq, ts, None, types, accts))
            i += 1
    # Shuffle the *list order* (processing order is decided by (ts, seq), so a
    # correct solution must sort; ids/seqs stay unique).
    rng.shuffle(ops)
    return ops


def _mk_op(rng, id_, seq, ts, group, types, accts):
    t = rng.choice(types)
    amt = rng.randint(1, 120)  # always > 0
    if t == "transfer":
        src = rng.choice(accts)
        dst = rng.choice(accts)
        return _op(id_, seq, ts, t, group, src=src, dst=dst, amt=amt)
    return _op(id_, seq, ts, t, group, acct=rng.choice(accts), amt=amt)


# Generated once at import with fixed seeds (committed determinism).
_ORACLE_CASES = [
    _rand_oplist(seed=s, n_ops=n, n_accts=a, p_group=pg, max_ts=mt)
    for (s, n, a, pg, mt) in [
        (1, 40, 4, 0.35, 6),
        (2, 60, 5, 0.50, 8),
        (3, 80, 3, 0.40, 5),   # few accounts -> more contention -> more rejects/rollbacks
        (4, 50, 6, 0.30, 10),
        (5, 120, 4, 0.55, 7),
        (6, 30, 2, 0.60, 4),   # tiny + dense groups
    ]
]


def _big_gate_oplist():
    """Deterministic ~50k-op instance for the hard time gate (fixed seed)."""
    return _rand_oplist(seed=GATE_SEED, n_ops=GATE_N, n_accts=2000,
                        p_group=0.4, max_ts=GATE_N)


def _pairs(res: dict):
    """Normalise accounts dict to a comparable {acct: (balance, held)} mapping."""
    return {a: (v["balance"], v["held"]) for a, v in res["accounts"].items()}


# ===========================================================================
# Tests
# ===========================================================================

# --- 1. Return shape & keys -------------------------------------------------
def test_return_shape_and_keys():
    res = replay(_worked_example())
    assert isinstance(res, dict)
    assert set(res.keys()) == {"accounts", "rejected"}
    assert isinstance(res["accounts"], dict)
    assert isinstance(res["rejected"], list)
    for v in res["accounts"].values():
        assert set(v.keys()) == {"balance", "held"}
        assert isinstance(v["balance"], int) and isinstance(v["held"], int)
    assert all(isinstance(x, int) for x in res["rejected"])


# --- 2. Worked example (exact) ---------------------------------------------
def test_worked_example_exact():
    res = replay(_worked_example())
    assert _pairs(res) == {"A": (100, 60), "B": (50, 0), "C": (0, 0)}
    assert res["rejected"] == [13, 14, 15, 16]


# --- 3. [FAIL_TO_PASS] atomic-group rollback restores balance, held, and the
#         transfer dst when a later member of the group is rejected. ----------
def test_group_rollback_restores_balance_held_and_transfer():
    # ts=1 deposits set the stage; the ts=2 group's 3rd op fails, so the hold
    # (held) and the transfer (src balance + dst balance) must BOTH be undone.
    ops = [
        _op(1, 1, 1, "deposit", None, acct="X", amt=200),
        _op(2, 2, 1, "deposit", None, acct="Y", amt=40),
        # atomic group at ts=2, group=7 (seq 3,4,5)
        _op(3, 3, 2, "hold", 7, acct="X", amt=50),          # ok -> held[X]=50
        _op(4, 4, 2, "transfer", 7, src="X", dst="Z", amt=30),  # ok -> X 170, Z 30
        _op(5, 5, 2, "fee", 7, acct="Y", amt=999),          # FAIL: available[Y]=40<999
    ]
    res = replay(ops)
    # Whole group rolled back: held[X] back to 0, X balance back to 200, Z=0.
    assert _pairs(res) == {"X": (200, 0), "Y": (40, 0), "Z": (0, 0)}
    assert res["rejected"] == [3, 4, 5]
    assert res == _oracle(ops)


# --- 4. [FAIL_TO_PASS] a successful hold inside a later-failing group is undone
#         (isolates the held-restore part of rollback). -----------------------
def test_group_rollback_restores_held_specifically():
    ops = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=100),
        _op(2, 2, 2, "hold", 5, acct="A", amt=60),       # ok in-group -> held 60
        _op(3, 3, 2, "withdraw", 5, acct="A", amt=50),   # available 40 < 50 -> FAIL
    ]
    res = replay(ops)
    # held must be restored to 0 (not left at 60).
    assert _pairs(res) == {"A": (100, 0)}
    assert res["rejected"] == [2, 3]
    assert res == _oracle(ops)


# --- 5. available vs balance: a standalone hold makes a later withdraw reject
#         even though balance >= amt. ------------------------------------------
def test_available_vs_balance_independent():
    ops = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=100),
        _op(2, 2, 2, "hold", None, acct="A", amt=70),    # available 30
        _op(3, 3, 3, "withdraw", None, acct="A", amt=50),  # 30<50 -> reject (balance 100 though)
        _op(4, 4, 4, "withdraw", None, acct="A", amt=30),  # 30>=30 -> ok, balance 70
    ]
    res = replay(ops)
    assert _pairs(res) == {"A": (70, 70)}
    assert res["rejected"] == [3]
    assert res == _oracle(ops)


# --- 6. processing order is (ts, seq): ops given out of list order ----------
def test_processing_order_ts_then_seq():
    # Deliberately interleaved seq/ts and shuffled list order. A deposit at a
    # LATER ts must not fund an earlier-ts withdraw.
    ops = [
        _op(3, 30, 5, "withdraw", None, acct="A", amt=100),  # ts5: needs funds first
        _op(1, 10, 1, "deposit", None, acct="A", amt=40),    # ts1
        _op(2, 20, 3, "deposit", None, acct="A", amt=80),    # ts3 -> balance 120 by ts5
        _op(4, 40, 0, "withdraw", None, acct="A", amt=10),   # ts0: BEFORE any deposit -> reject
    ]
    res = replay(ops)
    # ts0 withdraw rejected (balance 0); ts1 +40, ts3 +80 -> 120; ts5 withdraw 100 ok -> 20.
    assert _pairs(res) == {"A": (20, 0)}
    assert res["rejected"] == [4]  # only the ts0 op; in processing order
    assert res == _oracle(ops)


# --- 7. independent (group None) ops are each isolated ----------------------
def test_independent_ops_isolated():
    # A rejected independent op must not affect neighbours; each stands alone.
    ops = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=50),
        _op(2, 2, 2, "withdraw", None, acct="A", amt=999),  # reject, no effect
        _op(3, 3, 3, "deposit", None, acct="A", amt=10),    # still applies -> 60
        _op(4, 4, 4, "withdraw", None, acct="A", amt=60),   # ok -> 0
    ]
    res = replay(ops)
    assert _pairs(res) == {"A": (0, 0)}
    assert res["rejected"] == [2]
    assert res == _oracle(ops)


# --- 8. transfer auto-creates dst; dst appears in accounts ------------------
def test_transfer_creates_dst():
    ops = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=100),
        _op(2, 2, 2, "transfer", None, src="A", dst="NEW", amt=40),
    ]
    res = replay(ops)
    assert _pairs(res) == {"A": (60, 0), "NEW": (40, 0)}
    assert res["rejected"] == []
    # An account touched only by a REJECTED op still appears.
    ops2 = [_op(1, 1, 1, "transfer", None, src="P", dst="Q", amt=5)]  # P has 0 -> reject
    res2 = replay(ops2)
    assert _pairs(res2) == {"P": (0, 0), "Q": (0, 0)}
    assert res2["rejected"] == [1]


# --- 9. all-success group commits ------------------------------------------
def test_all_success_group_commits():
    ops = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=100),
        _op(2, 2, 2, "hold", 9, acct="A", amt=20),       # ok -> held 20
        _op(3, 3, 2, "transfer", 9, src="A", dst="B", amt=30),  # available 80 -> ok
        _op(4, 4, 2, "release", 9, acct="A", amt=20),    # ok -> held 0
    ]
    res = replay(ops)
    # group commits: A balance 70, held 0; B 30.
    assert _pairs(res) == {"A": (70, 0), "B": (30, 0)}
    assert res["rejected"] == []
    assert res == _oracle(ops)


# --- 10. grouping needs equal ts AND equal group ----------------------------
def test_grouping_requires_equal_ts_and_group():
    # Same group=1 but DIFFERENT ts -> NOT one atomic unit; each is its own
    # singleton. The first (a hold that succeeds) must NOT be rolled back when
    # the second (a withdraw that fails) is rejected.
    ops = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=100),
        _op(2, 2, 2, "hold", 1, acct="A", amt=60),       # ts2, group1
        _op(3, 3, 3, "withdraw", 1, acct="A", amt=80),   # ts3, group1: available 40<80 -> reject
    ]
    res = replay(ops)
    # hold is NOT in the same group as the withdraw (different ts) -> it stays.
    assert _pairs(res) == {"A": (100, 60)}
    assert res["rejected"] == [3]
    assert res == _oracle(ops)

    # Same ts but DIFFERENT group -> two distinct atomic groups; one failing must
    # not roll back the other.
    ops2 = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=100),
        _op(2, 2, 2, "transfer", 1, src="A", dst="B", amt=30),  # group1: ok
        _op(3, 3, 2, "withdraw", 2, acct="A", amt=999),         # group2: fail, isolated
    ]
    res2 = replay(ops2)
    assert _pairs(res2) == {"A": (70, 0), "B": (30, 0)}
    assert res2["rejected"] == [3]
    assert res2 == _oracle(ops2)


# --- 11. rejected-id ordering across mixed groups & singletons --------------
def test_rejected_id_ordering_mixed():
    # Two failing groups and two failing singletons across several ts; rejected
    # must follow processing order (units by earliest (ts, seq)), group ids
    # contiguous & in seq order.
    ops = [
        _op(100, 1, 1, "withdraw", None, acct="A", amt=5),   # ts1 singleton: fail
        _op(200, 2, 2, "hold", 1, acct="A", amt=5),          # ts2 group1
        _op(201, 3, 2, "withdraw", 1, acct="A", amt=5),      # ts2 group1: fail -> [200,201]
        _op(300, 4, 3, "withdraw", None, acct="B", amt=5),   # ts3 singleton: fail
        _op(400, 5, 4, "transfer", 2, src="C", dst="D", amt=5),  # ts4 group2
        _op(401, 6, 4, "fee", 2, acct="C", amt=5),               # ts4 group2: fail -> [400,401]
    ]
    res = replay(ops)
    assert res["rejected"] == [100, 200, 201, 300, 400, 401]
    assert res == _oracle(ops)


# --- 12. validation: ValueError on amt<=0, unknown type, dup id, dup seq ----
def test_validation_errors():
    base = _op(1, 1, 1, "deposit", None, acct="A", amt=100)
    # amt <= 0
    with pytest.raises(ValueError):
        replay([_op(1, 1, 1, "deposit", None, acct="A", amt=0)])
    with pytest.raises(ValueError):
        replay([_op(1, 1, 1, "withdraw", None, acct="A", amt=-5)])
    # unknown type
    with pytest.raises(ValueError):
        replay([_op(1, 1, 1, "frobnicate", None, acct="A", amt=5)])
    # missing required field (no amt)
    with pytest.raises(ValueError):
        replay([{"id": 1, "seq": 1, "ts": 1, "type": "deposit", "group": None, "acct": "A"}])
    # missing base field (no group key at all)
    with pytest.raises(ValueError):
        replay([{"id": 1, "seq": 1, "ts": 1, "type": "deposit", "acct": "A", "amt": 5}])
    # duplicate id
    with pytest.raises(ValueError):
        replay([base, _op(1, 2, 2, "deposit", None, acct="B", amt=5)])
    # duplicate seq
    with pytest.raises(ValueError):
        replay([base, _op(2, 1, 2, "deposit", None, acct="B", amt=5)])


# --- 13. empty input --------------------------------------------------------
def test_empty_input():
    res = replay([])
    assert res == {"accounts": {}, "rejected": []}


# --- 14. release rule tests held (not available) ----------------------------
def test_release_checks_held():
    ops = [
        _op(1, 1, 1, "deposit", None, acct="A", amt=100),
        _op(2, 2, 2, "hold", None, acct="A", amt=40),    # held 40
        _op(3, 3, 3, "release", None, acct="A", amt=50),  # held 40 < 50 -> reject
        _op(4, 4, 4, "release", None, acct="A", amt=40),  # ok -> held 0
    ]
    res = replay(ops)
    assert _pairs(res) == {"A": (100, 0)}
    assert res["rejected"] == [3]
    assert res == _oracle(ops)


# --- 15. independent oracle on several seeded pseudo-random op-lists --------
@pytest.mark.parametrize("idx", list(range(len(_ORACLE_CASES))))
def test_matches_independent_oracle(idx):
    ops = _ORACLE_CASES[idx]
    got = replay(ops)
    exp = _oracle(ops)
    # Compare both fields (account map order is unspecified).
    assert got["rejected"] == exp["rejected"], (idx, got["rejected"], exp["rejected"])
    assert _pairs(got) == _pairs(exp), idx
    # Sanity: the case actually exercises groups and at least one rollback.
    assert any(o["group"] is not None for o in ops)


def test_oracle_cases_exercise_rollback():
    """Guard: across the seeded corpus there is at least one rolled-back group
    (otherwise the FAIL_TO_PASS behaviour would be untested by the oracle)."""
    saw_rollback = False
    for ops in _ORACLE_CASES:
        exp = _oracle(ops)
        # A rolled-back group contributes >=2 contiguous rejected ids that share
        # a (ts, group); detecting any group with all members rejected suffices.
        by_group: dict[tuple, list[int]] = {}
        for o in ops:
            if o["group"] is not None:
                by_group.setdefault((o["ts"], o["group"]), []).append(o["id"])
        rej = set(exp["rejected"])
        for members in by_group.values():
            if len(members) >= 2 and all(m in rej for m in members):
                saw_rollback = True
                break
        if saw_rollback:
            break
    assert saw_rollback, "seeded oracle corpus never triggers a group rollback"


# --- 16. HARD time gate: ~50k ops, fixed seed, 6s budget -------------------
def test_hard_time_gate():
    """A deterministic ~50,000-op instance must replay within 6 seconds.

    The intended O(n log n) staging solution finishes in well under a second.
    An O(n^2) approach (re-replaying history to undo a rejected group) blows the
    budget and is rejected.
    """
    big = _big_gate_oplist()
    assert len(big) == GATE_N
    res = gu.run_within(GATE_TIMEOUT, replay, big)
    # Shape sanity on the result of the gated run.
    assert isinstance(res, dict) and set(res.keys()) == {"accounts", "rejected"}
    assert isinstance(res["rejected"], list)
    assert all(isinstance(x, int) for x in res["rejected"])
    # Every touched account has integer balance/held; held is never negative and
    # balance - held is never negative (no rule can drive available below 0).
    for v in res["accounts"].values():
        assert isinstance(v["balance"], int) and isinstance(v["held"], int)
        assert v["held"] >= 0
        assert v["balance"] - v["held"] >= 0


# --- 17. SOFT complexity signal (advisory) ----------------------------------
@pytest.mark.soft_complexity
def test_soft_complexity():
    """Empirical fit — advisory only; fails only if the estimate is >2 tiers
    above the O(n log n) target. The hard gate is the real discriminator."""
    sizes = [2000, 4000, 8000, 16000]

    def make_input(n: int):
        return _rand_oplist(seed=n, n_ops=n, n_accts=max(50, n // 20),
                            p_group=0.4, max_ts=n)

    timings = gu.measure_runtime(make_input, replay, sizes, repeats=2)
    report = gu.estimate_time_complexity(timings)
    print(f"[soft_complexity] estimated={report['label']}  target=O(n log n)  "
          f"ranked={report['ranked'][:3]}")
    assert gu.within_one_tier(report["label"], "O(n log n)"), (
        f"soft complexity: estimated {report['label']} is more than one tier "
        "above O(n log n); strong signal of a wrong (super-linearithmic) algorithm."
    )


# --- 18. Advisory code-quality report (never asserted) ----------------------
@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
