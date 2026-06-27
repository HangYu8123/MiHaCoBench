from accounts import Account
from transactions import post_entries


class Ledger:
    def __init__(self) -> None:
        """An empty ledger with no accounts."""
        self._accounts: dict = {}

    def add_account(self, name: str) -> None:
        """Create a new zero-balance Account named `name`.

        Raises ValueError if an account with that name already exists.
        """
        if name in self._accounts:
            raise ValueError(f"Account '{name}' already exists.")
        self._accounts[name] = Account(name)

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
        # Validate all amounts sum to zero
        total = sum(amount for _, amount in entries)
        if total != 0:
            raise ValueError("entries must balance")

        # Validate all account names exist (raises KeyError if not)
        for name, _ in entries:
            if name not in self._accounts:
                raise KeyError(name)

        # Delegate to post_entries
        post_entries(entries, self._accounts)

    def balance(self, name: str) -> int:
        """Return the integer-cent balance of account `name`
        (KeyError if no such account)."""
        if name not in self._accounts:
            raise KeyError(name)
        return self._accounts[name].balance

    def trial_balance(self) -> int:
        """Return the sum of all account balances.

        After ANY balanced posting this must be exactly 0 — every debit is
        matched by an equal credit.
        """
        return sum(account.balance for account in self._accounts.values())
