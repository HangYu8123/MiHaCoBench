"""Gold reference for harness/h06_replay_ledger.

Replay a stream of ledger operations and return the final account state plus the
ids of every rejected operation, in processing order.

All amounts are integer numbers of cents (``int``); no floats are involved.

Semantics (see TASK.md for the full contract):

  * Operations are processed in ``(ts, seq)`` ascending order (``seq`` is a
    globally unique total tie-break).
  * Each account has ``balance`` and ``held``; ``available = balance - held``.
    An account referenced for the first time is implicitly ``balance=0,
    held=0``.
  * ``deposit / withdraw / transfer / hold / release / fee`` apply with the
    per-op success conditions in the contract; an op that fails its condition is
    *rejected*.
  * Ops sharing the SAME ``ts`` AND the SAME non-``None`` ``group`` form one
    ATOMIC group applied in ``seq`` order: if any op in the group is rejected,
    the ENTIRE group rolls back (no op leaves any effect) and every op id is
    recorded as rejected. Ops with ``group is None`` are independent units.

Efficiency: ``O(n log n)`` for the sort plus amortized ``O(1)`` work per op.
Atomic rollback is done by *staging* — before a group runs we snapshot only the
``(balance, held)`` of the accounts that group touches, then restore exactly
those on failure. We never re-replay history, so 50k ops run comfortably within
the grader's time budget.
"""
from __future__ import annotations

from typing import Any

# Required fields per op type (besides the always-present id/seq/ts/type/group).
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
    """Validate the whole op stream up front, raising ``ValueError`` on any fault.

    Faults: unknown ``type``; any missing required field (base or type-specific);
    ``amt <= 0``; duplicate ``id``; duplicate ``seq``.
    """
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
    """Return the (creating if needed) state dict for ``acct``."""
    state = accounts.get(acct)
    if state is None:
        state = {"balance": 0, "held": 0}
        accounts[acct] = state
    return state


def _apply_one(accounts: dict[Any, dict[str, int]], op: dict) -> bool:
    """Apply a single op to the working state. Return True if it committed,
    False if it was rejected (in which case the state is left UNCHANGED for this
    op — every op either fully applies its own effect or makes none)."""
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
    """The accounts an op references (so they get touched / snapshotted)."""
    if op["type"] == "transfer":
        return (op["src"], op["dst"])
    return (op["acct"],)


def _units(order: list[dict]) -> list[list[dict]]:
    """Partition the (ts, seq)-sorted op list into processing UNITS.

    A unit is either a single ``group is None`` op or the maximal set of ops
    sharing one ``(ts, non-None group)`` (an atomic group). Within a group the
    ops keep ``seq`` order. Units are returned in processing order: by the
    smallest ``(ts, seq)`` of their member ops (so a group is processed at the
    position of its earliest op). This is a total, deterministic order because
    ``seq`` is globally unique.
    """
    # Bucket atomic-group members by (ts, group); remember each group's earliest
    # (ts, seq) so we can order units by their first op.
    groups: dict[tuple, list[dict]] = {}
    first_key: dict[tuple, tuple] = {}
    units: list[tuple[tuple, list[dict]]] = []  # (sort_key, ops)

    for op in order:  # already sorted by (ts, seq)
        group = op["group"]
        if group is None:
            units.append(((op["ts"], op["seq"]), [op]))
            continue
        key = (op["ts"], group)
        bucket = groups.get(key)
        if bucket is None:
            bucket = []
            groups[key] = bucket
            first_key[key] = (op["ts"], op["seq"])  # first seen == smallest seq for this ts
            units.append((first_key[key], bucket))
        bucket.append(op)  # appended in (ts, seq) order -> seq order within the group

    units.sort(key=lambda u: u[0])
    return [ops for _key, ops in units]


def replay(ops: list[dict]) -> dict:
    """Replay ``ops`` and return ``{"accounts": {...}, "rejected": [...]}``.

    See the module docstring and TASK.md for the full contract.
    """
    _validate(ops)

    # Total processing order: (ts, seq) ascending; seq is globally unique.
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

        # Atomic group. Snapshot the (balance, held) of every account it touches
        # (creating them first so a rolled-back group still leaves its accounts
        # present in the output), apply in seq order, and on any rejection
        # restore exactly those accounts and reject every id in seq order.
        snapshot: dict[Any, tuple[int, int]] = {}
        for op in unit:
            for a in _accts_of(op):
                s = _touch(accounts, a)
                if a not in snapshot:
                    snapshot[a] = (s["balance"], s["held"])

        ok = True
        for op in unit:
            if not _apply_one(accounts, op):
                ok = False
                break

        if not ok:
            for a, (bal, held) in snapshot.items():
                s = accounts[a]
                s["balance"] = bal
                s["held"] = held
            for op in unit:
                rejected.append(op["id"])

    out_accounts = {
        acct: {"balance": s["balance"], "held": s["held"]}
        for acct, s in accounts.items()
    }
    return {"accounts": out_accounts, "rejected": rejected}
