# SWE-Bench 05 — `ledger_balance`: Double-Entry Ledger Across 3 Modules

**Created:** 2026-06-16 · **Category:** swe_bench · **Weight:** 6

Implement a small **double-entry ledger** in integer cents, split across three
modules. A symptom is observed at the facade (`ledger.py`) — debited accounts
do not move and the trial balance fails to net to zero — but the **root cause
lives in `transactions.py`**, one module boundary away. This is an SWE-bench
style multi-file fault-localisation task: the bug is invisible at the layer
where it is observed.

```
accounts.py      — class Account
transactions.py  — function post_entries   (the bug lives in this file)
ledger.py        — FACADE: class Ledger (validates, then delegates)
```

---

## Files to create

```
accounts.py      — class Account
transactions.py  — function post_entries(entries, accounts)
ledger.py        — FACADE: class Ledger; re-exports Ledger
```

All three modules use **stdlib only** — no third-party packages.

---

## Public contract

### `accounts.py`

```python
class Account:
    def __init__(self, name: str) -> None:
        """A named account whose integer-cent balance starts at 0."""

    def apply(self, amount_cents: int) -> None:
        """Add the signed amount_cents to this account's balance.

        A positive amount credits the account; a negative amount debits it.
        Balances are plain Python ints (cents) — no floats anywhere.
        """
```

The current balance is readable as the attribute `balance` (an `int`).

### `transactions.py`

```python
def post_entries(entries, accounts) -> None:
    """Apply EVERY entry to its account.

    entries  : a list of (account_name: str, amount_cents: int) pairs with
               signed integer amounts (debit = negative, credit = positive).
    accounts : a dict mapping name -> Account.

    For each (name, amount) pair, call accounts[name].apply(amount).
    EVERY entry must be applied — both debits and credits.
    """
```

This function performs no validation; that is the facade's job (below).

### `ledger.py` (facade)

```python
class Ledger:
    def __init__(self) -> None:
        """An empty ledger with no accounts."""

    def add_account(self, name: str) -> None:
        """Create a new zero-balance Account named `name`.

        Raises ValueError if an account with that name already exists.
        """

    def post(self, entries) -> None:
        """Validate, then post a balanced set of (name, amount_cents) entries.

        Validation (performed BEFORE any account is mutated):
          * the signed amounts must sum to exactly 0; otherwise raise
            ValueError("entries must balance").
          * every referenced account name must already exist; otherwise
            raise KeyError.

        After validation, delegate to transactions.post_entries, which applies
        every entry to its account.
        """

    def balance(self, name: str) -> int:
        """Return the integer-cent balance of account `name`
        (KeyError if no such account)."""

    def trial_balance(self) -> int:
        """Return the sum of all account balances.

        After ANY balanced posting this must be exactly 0 — every debit is
        matched by an equal credit.
        """
```

`ledger.py` must re-export `Ledger` so the grader can do:

```python
from ledger import Ledger
```

---

## Expected behaviour (worked example)

```python
led = Ledger()
led.add_account("A")
led.add_account("B")
led.post([("A", -100), ("B", 100)])   # transfer 100 cents A -> B

led.balance("A")        # == -100   (A was debited)
led.balance("B")        # ==  100   (B was credited)
led.trial_balance()     # ==    0   (debits net against credits)
```

All amounts are **exact integers (cents)**; compare with `==` on ints, never
floats.

---

## Known bug description (for SWE-bench fault localisation)

The symptom appears at the `ledger.py` facade: after a balanced posting, the
**debited** account never changes and `trial_balance()` is non-zero (e.g.
`100` instead of `0`) — yet `post()`'s validation (sum of entries == 0) passes
because it sums the *original* entries. The root cause is **not** in `ledger.py`
or `accounts.py`: it is in `transactions.py`, where `post_entries` silently
**drops every entry with a negative (debit) amount** instead of applying it. So
credits post but matching debits are ignored, leaving the books out of balance.

**Your task:** fix `transactions.py` so that `post_entries` applies *every*
entry — debits and credits alike — so a balanced transfer moves both accounts
and `trial_balance()` returns to 0.

---

## Constraints

- Use **stdlib only** — no third-party packages.
- All balances and amounts are **integer cents**; no floating-point arithmetic.
- `post()` validates (balance-to-zero and account existence) *before* mutating
  any account.
- The grader imports `Ledger` from `ledger.py` only.
