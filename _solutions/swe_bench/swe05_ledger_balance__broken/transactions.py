"""transactions.py — the low-level entry-posting routine.

This module knows nothing about validation; the :class:`Ledger` facade in
``ledger.py`` is responsible for checking that entries balance and that the
referenced accounts exist before delegating here. ``post_entries`` simply walks
every entry and applies the signed amount to the named account.
"""
from __future__ import annotations

from typing import Iterable, Tuple

from accounts import Account


def post_entries(
    entries: Iterable[Tuple[str, int]],
    accounts: dict[str, Account],
) -> None:
    """Apply EVERY ``(account_name, amount_cents)`` entry to its account.

    ``entries`` is an iterable of ``(name, amount)`` pairs with signed integer
    cent amounts. For each pair this calls ``accounts[name].apply(amount)`` so
    that debits (negative) and credits (positive) both post.
    """
    for name, amount in entries:
        # BUG: negative (debit) entries are silently skipped, so only credits
        # post. Validation in ledger.py still passes because it sums the
        # ORIGINAL entries, which do balance — the fault is invisible until you
        # inspect the resulting account balances.
        if amount < 0:
            continue
        accounts[name].apply(amount)
