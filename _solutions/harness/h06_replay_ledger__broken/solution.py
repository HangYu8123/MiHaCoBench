"""BROKEN reference for harness/h06_replay_ledger.

PLANTED DEFECT (localized to atomic-group rollback): the ops of an atomic group
are applied IMMEDIATELY to the live state, and on a rejection inside the group
every id is still recorded as rejected BUT only the FAILING op's (no-op) effect
is undone — the earlier ops of the group that already succeeded (a committed
hold, a committed transfer, ...) are left applied. There is no real rollback.

Consequences:
  * a group whose 3rd op fails leaves the effects of its first two ops in place
    (e.g. a hold stays held and a transfer's cents stay moved), so balances/held
    are wrong even though all three ids are (correctly) reported as rejected.

Everything else is correct: validation, processing order, independent (group
None) ops, all-success groups, transfer auto-creating dst, and the rejected-id
ordering. So non-group cases and all-success-group cases pass; only the
partial-rollback case fails.
"""
from __future__ import annotations

from typing import Any

_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "deposit": ("acct", "amt"),
    "withdraw": ("acct", "amt"),
    "transfer": ("src", "dst", "amt"),
    "hold": ("acct", "amt"),
    "release": ("acct", "amt"),
    "fee": ("acct", "amt"),
}

_BASE_FIELDS = ("id", "seq", "ts", "type", "group")


def _validate(ops: list[dict]) -> None:
    seen_ids: set = set()
    seen_seqs: set = set()
    for op in ops:
        for f in _BASE_FIELDS:
            if f not in op:
                raise ValueError(f"missing required field {f!r}")
        op_type = op["type"]
        if op_type not in _REQUIRED_FIELDS:
            raise ValueError(f"unknown op type {op_type!r}")
        for f in _REQUIRED_FIELDS[op_type]:
            if f not in op:
                raise ValueError(f"missing required field {f!r} for {op_type!r}")
        amt = op["amt"]
        if amt <= 0:
            raise ValueError(f"amt must be > 0, got {amt!r}")

        op_id = op["id"]
        if op_id in seen_ids:
            raise ValueError(f"duplicate id {op_id!r}")
        seen_ids.add(op_id)

        seq = op["seq"]
        if seq in seen_seqs:
            raise ValueError(f"duplicate seq {seq!r}")
        seen_seqs.add(seq)


def _touch(accounts: dict[Any, dict[str, int]], acct: Any) -> dict[str, int]:
    state = accounts.get(acct)
    if state is None:
        state = {"balance": 0, "held": 0}
        accounts[acct] = state
    return state


def _apply_one(accounts: dict[Any, dict[str, int]], op: dict) -> bool:
    op_type = op["type"]
    amt = op["amt"]

    if op_type == "deposit":
        _touch(accounts, op["acct"])["balance"] += amt
        return True

    if op_type == "withdraw":
        s = _touch(accounts, op["acct"])
        if s["balance"] - s["held"] < amt:
            return False
        s["balance"] -= amt
        return True

    if op_type == "transfer":
        src = _touch(accounts, op["src"])
        dst = _touch(accounts, op["dst"])
        if src["balance"] - src["held"] < amt:
            return False
        src["balance"] -= amt
        dst["balance"] += amt
        return True

    if op_type == "hold":
        s = _touch(accounts, op["acct"])
        if s["balance"] - s["held"] < amt:
            return False
        s["held"] += amt
        return True

    if op_type == "release":
        s = _touch(accounts, op["acct"])
        if s["held"] < amt:
            return False
        s["held"] -= amt
        return True

    # fee
    s = _touch(accounts, op["acct"])
    if s["balance"] - s["held"] < amt:
        return False
    s["balance"] -= amt
    return True


def _accts_of(op: dict) -> tuple:
    if op["type"] == "transfer":
        return (op["src"], op["dst"])
    return (op["acct"],)


def _units(order: list[dict]) -> list[list[dict]]:
    groups: dict[tuple, list[dict]] = {}
    first_key: dict[tuple, tuple] = {}
    units: list[tuple[tuple, list[dict]]] = []

    for op in order:
        group = op["group"]
        if group is None:
            units.append(((op["ts"], op["seq"]), [op]))
            continue
        key = (op["ts"], group)
        bucket = groups.get(key)
        if bucket is None:
            bucket = []
            groups[key] = bucket
            first_key[key] = (op["ts"], op["seq"])
            units.append((first_key[key], bucket))
        bucket.append(op)

    units.sort(key=lambda u: u[0])
    return [ops for _key, ops in units]


def replay(ops: list[dict]) -> dict:
    _validate(ops)

    order = sorted(ops, key=lambda o: (o["ts"], o["seq"]))

    accounts: dict[Any, dict[str, int]] = {}
    rejected: list[int] = []

    for unit in _units(order):
        if len(unit) == 1 and unit[0]["group"] is None:
            op = unit[0]
            for a in _accts_of(op):
                _touch(accounts, a)
            if not _apply_one(accounts, op):
                rejected.append(op["id"])
            continue

        # BUG: apply group ops live, and on rejection only the failing op's
        # (no-op) effect is "undone" (there is nothing to undo for it). The
        # earlier, already-committed ops of the group are NOT rolled back.
        for a in (acc for op in unit for acc in _accts_of(op)):
            _touch(accounts, a)

        ok = True
        for op in unit:
            if not _apply_one(accounts, op):
                ok = False
                break

        if not ok:
            # No real rollback: prior ops stay applied. Only the ids are recorded.
            for op in unit:
                rejected.append(op["id"])

    out_accounts = {
        acct: {"balance": s["balance"], "held": s["held"]}
        for acct, s in accounts.items()
    }
    return {"accounts": out_accounts, "rejected": rejected}
