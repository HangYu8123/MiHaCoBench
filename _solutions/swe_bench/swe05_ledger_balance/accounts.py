"""accounts.py — the Account value object for the double-entry ledger.

An Account tracks a single integer-cent balance. Amounts are signed: a debit is
a negative ``amount_cents`` and a credit is a positive one. All arithmetic is in
integer cents so there is never any floating-point rounding error.
"""
from __future__ import annotations


class Account:
    """A named account holding an integer-cent balance (starts at 0)."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.balance = 0

    def apply(self, amount_cents: int) -> None:
        """Add the signed ``amount_cents`` to this account's balance.

        A positive amount credits the account; a negative amount debits it.
        """
        self.balance += amount_cents

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return f"Account(name={self.name!r}, balance={self.balance})"
