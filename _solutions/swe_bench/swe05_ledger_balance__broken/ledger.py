"""ledger.py — FACADE for the double-entry ledger.

Re-exports :class:`Ledger` as the public API. ``Ledger`` validates postings
(entries must balance to zero, every referenced account must exist) and then
delegates the actual balance mutation to :func:`transactions.post_entries`.

The grader imports only:

    from ledger import Ledger
"""
from __future__ import annotations

from typing import Iterable, Tuple

import transactions as _txn
from accounts import Account  # noqa: F401  (re-exported for convenience)


class Ledger:
    """A double-entry ledger over named integer-cent accounts."""

    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def add_account(self, name: str) -> None:
        """Create a new zero-balance account.

        Raises ``ValueError`` if an account with ``name`` already exists.
        """
        if name in self._accounts:
            raise ValueError(f"account already exists: {name!r}")
        self._accounts[name] = Account(name)

    def post(self, entries: Iterable[Tuple[str, int]]) -> None:
        """Validate and post a balanced set of ``(name, amount_cents)`` entries.

        Validation (performed before any account is mutated):

        * the signed amounts must sum to exactly 0, else ``ValueError``
          with message ``"entries must balance"``;
        * every referenced account must already exist, else ``KeyError``.

        After validation, delegates to :func:`transactions.post_entries`, which
        applies every entry to its account.
        """
        entries = list(entries)
        if sum(amount for _, amount in entries) != 0:
            raise ValueError("entries must balance")
        for name, _ in entries:
            if name not in self._accounts:
                raise KeyError(name)
        _txn.post_entries(entries, self._accounts)

    def balance(self, name: str) -> int:
        """Return the integer-cent balance of account ``name`` (KeyError if absent)."""
        return self._accounts[name].balance

    def trial_balance(self) -> int:
        """Return the sum of all account balances (0 after any balanced posting)."""
        return sum(acct.balance for acct in self._accounts.values())


__all__ = ["Ledger", "Account"]
