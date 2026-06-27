"""ledger.py — Facade for the double-entry ledger.

Imports and re-exports Ledger so callers can do:
    from ledger import Ledger
"""

from accounts import Account
from transactions import post_entries


class Ledger:
    def __init__(self) -> None:
        """An empty ledger with no accounts."""
        self._accounts: dict[str, Account] = {}

    def add_account(self, name: str) -> None:
        """Create a new zero-balance Account named ``name``.

        Raises ValueError if an account with that name already exists.
        """
        if name in self._accounts:
            raise ValueError(f"account already exists: {name!r}")
        self._accounts[name] = Account(name)

    def post(self, entries) -> None:
        """Validate, then post a balanced set of (name, amount_cents) entries.

        Validation (performed BEFORE any account is mutated):
          * every referenced account name must already exist; otherwise
            raise KeyError.
          * the signed amounts must sum to exactly 0; otherwise raise
            ValueError("entries must balance").

        After validation, delegate to transactions.post_entries, which applies
        every entry to its account.
        """
        # Validate account existence first so we raise KeyError before
        # the balance check (and definitely before any mutation).
        for name, _amount in entries:
            if name not in self._accounts:
                raise KeyError(name)

        # Validate that the entry set is balanced.
        if sum(amount for _name, amount in entries) != 0:
            raise ValueError("entries must balance")

        # All checks passed — delegate to post_entries (no mutation above).
        post_entries(entries, self._accounts)

    def balance(self, name: str) -> int:
        """Return the integer-cent balance of account ``name``
        (KeyError if no such account)."""
        return self._accounts[name].balance

    def trial_balance(self) -> int:
        """Return the sum of all account balances.

        After ANY balanced posting this must be exactly 0 — every debit is
        matched by an equal credit.
        """
        return sum(account.balance for account in self._accounts.values())
