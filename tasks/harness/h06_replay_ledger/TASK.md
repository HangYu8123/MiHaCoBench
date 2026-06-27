# Harness 06 — `replay`: Atomic Ledger Replay with Holds and Group Rollback

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 6

Replay a stream of ledger operations and return the final state. Several
interacting rules must hold at once: an `available = balance - held` notion that
makes a *hold* able to block a later withdrawal, and **atomic groups** that must
be **rolled back as a whole** when any member operation is rejected. Misreading
any one rule corrupts balances or the rejected list.

Implement your solution in a single file `solution.py` exposing the function
below. Use only the Python standard library (no third-party packages). **Every
amount is an integer number of cents (`int`); there are no floats anywhere.**

## Public contract

### `replay(ops: list[dict]) -> dict`

Replay the operations in `ops` and return the final ledger state.

Each op is a dict with these keys, plus type-specific fields:

| Key | Type | Meaning |
|-----|------|---------|
| `id` | `int` | Unique operation id. |
| `seq` | `int` | Globally unique sequence number (the total tie-break for ordering). |
| `ts` | `int` | Timestamp. |
| `type` | `str` | One of `deposit`, `withdraw`, `transfer`, `hold`, `release`, `fee`. |
| `group` | `int` or `None` | Atomic-group key (see below), or `None` for an independent op. |

**Account state.** Each account has a `balance` (`int`) and a `held` amount
(`int`). Define **`available = balance - held`**. An account that is referenced
by an op for the first time is treated as `balance=0, held=0` (and thereby comes
to exist once touched).

**Processing order.** Process ops sorted by `(ts, seq)` ascending. Because `seq`
is globally unique, this is a total order.

**Operation types** (each lists its extra fields and its **success
condition** — an op that fails its condition is *rejected* and, on its own,
changes nothing):

| `type` | Extra fields | Effect / rejection rule |
|--------|--------------|--------------------------|
| `deposit` | `acct`, `amt` | `balance[acct] += amt`. **Never** rejected (given `amt > 0`). |
| `withdraw` | `acct`, `amt` | Rejected if `available[acct] < amt`; else `balance[acct] -= amt`. |
| `transfer` | `src`, `dst`, `amt` | Rejected if `available[src] < amt`; else `balance[src] -= amt` **and** `balance[dst] += amt`. |
| `hold` | `acct`, `amt` | Rejected if `available[acct] < amt`; else `held[acct] += amt`. |
| `release` | `acct`, `amt` | Rejected if `held[acct] < amt`; else `held[acct] -= amt`. |
| `fee` | `acct`, `amt` | Rejected if `available[acct] < amt`; else `balance[acct] -= amt`. |

Note that `withdraw`, `transfer`, `hold`, and `fee` all test **`available`**
(not `balance`): an outstanding `hold` can make a withdrawal reject even when the
raw `balance` is large enough. `release` tests `held`.

**Atomic groups (the key rule).** Ops that share the **same `ts` AND the same
non-`None` `group`** form one **atomic group**. (Grouping requires **both** to be
equal: ops with the same `group` but different `ts` are **not** in the same
group; ops with the same `ts` but different `group` are different groups.) An op
whose `group is None` is its own independent unit.

Processing proceeds in **units**, where a unit is either a single `group is None`
op or one whole atomic group. **Units are processed in `(ts, seq)` order keyed by
the unit's earliest member** (a singleton's earliest member is itself; a group's
is its smallest-`seq` op). A group is therefore processed as one contiguous block
positioned at its earliest op.

Within an atomic group, evaluate the member ops **in `seq` order** against the
*working* state. If **every** member succeeds, the group **commits**. If **any**
member is rejected, the **entire group is rolled back** to the state it had
**before the group began** — so even members that individually succeeded leave
**no effect** (this includes restoring `held` changed by a `hold`/`release` and
restoring **both** sides of a `transfer`) — and **every** member op is recorded
as rejected.

**Validation.** Before processing, raise `ValueError` (aborting the whole
replay, returning nothing) if any of these holds for any op:

* `amt <= 0`;
* an unknown `type`;
* a missing required field (any of `id`, `seq`, `ts`, `type`, `group`, or a
  type-specific field listed above);
* a duplicate `id`;
* a duplicate `seq`.

**Return value.** A dict with **exactly** these two keys:

| Key | Type | Description |
|-----|------|-------------|
| `accounts` | `dict` | `{acct: {"balance": int, "held": int}}` for **every account that was touched** — referenced by any *processed* op, including as a transfer `dst`, and including accounts touched only by ops that were ultimately rejected. Key order is unspecified. |
| `rejected` | `list[int]` | The `id`s of rejected ops in **processing order** (`(ts, seq)`). For a rolled-back group, **all** of its member ids appear (contiguously, in `seq` order) at the group's processing position. |

Assert exception **types**; messages are unspecified.

## Worked example

```python
ops = [
    {"id": 10, "seq": 1, "ts": 1, "type": "deposit",  "group": None, "acct": "A", "amt": 100},
    {"id": 11, "seq": 2, "ts": 1, "type": "deposit",  "group": None, "acct": "B", "amt": 50},
    {"id": 12, "seq": 3, "ts": 2, "type": "hold",     "group": None, "acct": "A", "amt": 60},
    {"id": 13, "seq": 4, "ts": 3, "type": "withdraw", "group": None, "acct": "A", "amt": 50},
    {"id": 14, "seq": 5, "ts": 5, "type": "hold",     "group": 1,    "acct": "B", "amt": 30},
    {"id": 15, "seq": 6, "ts": 5, "type": "transfer", "group": 1,    "src": "A", "dst": "C", "amt": 20},
    {"id": 16, "seq": 7, "ts": 5, "type": "withdraw", "group": 1,    "acct": "B", "amt": 25},
]
replay(ops)
```

Step by step (processing order is already `(ts, seq)` here):

1. `id=10` deposit 100 → `A = {balance:100, held:0}`.
2. `id=11` deposit 50 → `B = {balance:50, held:0}`.
3. `id=12` hold 60 on `A` → `A = {balance:100, held:60}`, so `available[A] = 40`.
4. `id=13` **independent** withdraw 50 from `A`: `available[A] = 40 < 50` →
   **rejected** (even though `balance[A] = 100 ≥ 50`). `A` unchanged.
5. The atomic group `ts=5, group=1` (ids 14, 15, 16), in `seq` order:
   * `id=14` hold 30 on `B`: `available[B] = 50 ≥ 30` → succeeds; `held[B] = 30`.
   * `id=15` transfer 20 `A`→`C`: `available[A] = 100-60 = 40 ≥ 20` → succeeds;
     `balance[A] = 80`, `balance[C] = 20` (`C` is created as the `dst`).
   * `id=16` withdraw 25 from `B`: after the hold, `available[B] = 50 - 30 = 20`,
     and `20 < 25` → **rejected**.
   * Because one member was rejected, the **whole group rolls back**: the hold on
     `B` is undone (`held[B]` back to 0), the transfer is undone (`balance[A]`
     back to 100, `balance[C]` back to 0), and ids `14, 15, 16` are all recorded
     as rejected. `C` was touched, so it still exists (at `{balance:0, held:0}`).

Final result:

```python
{
    "accounts": {
        "A": {"balance": 100, "held": 60},
        "B": {"balance": 50,  "held": 0},
        "C": {"balance": 0,   "held": 0},
    },
    "rejected": [13, 14, 15, 16],
}
```

(`A` keeps its standalone hold of 60; the group's transfer that briefly set
`balance[A]=80` and `balance[C]=20`, and the hold that set `held[B]=30`, are all
undone by the rollback.)

## Scale

`ops` may contain up to **50,000** operations and the grader enforces a **hard
time budget of 6 seconds** on a deterministic ~50,000-op instance. An `O(n^2)`
approach — e.g. re-replaying history from the start to undo a rejected group —
times out. The intended solution is `O(n log n)` (one sort) plus amortized
`O(1)` work per op; roll a group back by snapshotting only the few accounts that
group touches and restoring exactly those on failure.

## Notes

* Integer cents only: every `balance`, `held`, and `amt` is an `int`. Do not use
  floats.
* Accounts may be identified by any hashable value (e.g. `int` or `str`).
* `deposit` is the only type that can never be rejected on its own.
* Determinism: the result is fully determined by `ops`; there is no randomness
  and no seed.
